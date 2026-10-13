import os
from ddgs import DDGS
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.graph.schemas import DocumentRelevance, HallucinationGrade
from src.graph.state import GraphState
from src.models import SearchResult
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever


class CRAGNodes:

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        model_name: str = "openai/gpt-oss-20b",
    ):
        self.retriever = retriever
        self.reranker = reranker

        # Free Groq LLM instance
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is missing. Get a free key at console.groq.com"
            )

        self.llm = ChatGroq(
            model=model_name,
            temperature=0.0,
            api_key=groq_api_key,
        )

        # Enforce structured output via tool calling
        self.doc_grader = self.llm.with_structured_output(DocumentRelevance)
        self.hallucination_grader = self.llm.with_structured_output(HallucinationGrade)

    def retrieve(self, state: GraphState) -> dict:
        """Node: Fetches candidates using hybrid search + cross-encoder re-ranking."""
        query_to_search = state.get("rewritten_query") or state["query"]
        tenant_id = state["tenant_id"]

        dense_hits = self.retriever.search_dense(tenant_id, query_to_search, top_k=10)
        sparse_hits = self.retriever.search_sparse(tenant_id, query_to_search, top_k=10)
        fused = self.retriever.reciprocal_rank_fusion(dense_hits, sparse_hits)
        reranked = self.reranker.rerank(query_to_search, fused, top_n=4)

        return {"documents": reranked}

    def grade_documents(self, state: GraphState) -> dict:
        """Node: Filters out irrelevant retrieved chunks via LLM evaluation."""
        query = state["query"]
        documents = state["documents"]

        prompt = ChatPromptTemplate.from_template(
            """You are a strict technical evaluator. Assess whether the following retrieved document 
contains relevant facts or keywords to answer the user query.

Query: {query}
Document: {document}

Provide a binary 'yes' or 'no' score indicating relevance."""
        )

        eval_chain = prompt | self.doc_grader
        relevant_docs: list[SearchResult] = []

        for doc in documents:
            try:
                res: DocumentRelevance = eval_chain.invoke(
                    {"query": query, "document": doc.content}
                )
                if res.binary_score.lower() == "yes":
                    relevant_docs.append(doc)
            except Exception as e:
                print(f"[Warning] Grader parse exception: {e}")
                relevant_docs.append(doc)

        relevance_status = "relevant" if relevant_docs else "insufficient"
        return {"documents": relevant_docs, "relevance_status": relevance_status}

    def rewrite_query(self, state: GraphState) -> dict:
        """Node: Decontextualizes and rewrites query to improve retrieval."""
        current_query = state.get("rewritten_query") or state["query"]
        loop_count = state.get("loop_count", 0) + 1

        prompt = ChatPromptTemplate.from_template(
            """The previous query failed to retrieve relevant documents. 
Analyze the query and rewrite it into an optimized search query using standard technical vocabulary, keywords, and error codes.

Original Query: {query}
Provide ONLY the rewritten query string without quotes or preamble:"""
        )

        chain = prompt | self.llm
        response = chain.invoke({"query": current_query})

        return {
            "rewritten_query": response.content.strip(),
            "loop_count": loop_count,
        }

    def fallback_search(self, state: GraphState) -> dict:
        """Node: Live fallback search using DDGS."""
        query = state.get("rewritten_query") or state["query"]
        fallback_results: list[SearchResult] = []

        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=3))

            print(f"--> [Fallback DDGS] Retrieved {len(raw_results)} external results for: '{query}'")

            for i, item in enumerate(raw_results):
                fallback_results.append(
                    SearchResult(
                        chunk_id=f"ddg_{i}",
                        doc_id="duckduckgo_fallback",
                        content=f"Title: {item.get('title', '')}\nSnippet: {item.get('body', '')}",
                        score=1.0,
                        source="duckduckgo_web",
                        metadata={"url": item.get("href", "")},
                    )
                )
        except Exception as e:
            print(f"--> [Fallback DDGS Error]: {e}")
            fallback_results.append(
                SearchResult(
                    chunk_id="ddg_err",
                    doc_id="fallback_err",
                    content=f"Web search unavailable. Query was: {query}",
                    score=0.0,
                    source="fallback_error",
                )
            )

        return {"documents": fallback_results, "relevance_status": "fallback"}

    def generate(self, state: GraphState) -> dict:
        """Node: Generates the grounded answer using verified context."""
        query = state["query"]
        docs = state["documents"]
        context_str = "\n\n".join([f"- {d.content}" for d in docs])

        prompt = ChatPromptTemplate.from_template(
            """You are a technical AI assistant. Answer the user's question using ONLY the context provided below.
If the context does not contain sufficient facts to answer, explicitly state that the documents do not provide this information.
Do NOT make up facts.

Context:
{context}

Question: {question}
Answer:"""
        )

        chain = prompt | self.llm
        response = chain.invoke({"context": context_str, "question": query})

        return {"generation": response.content.strip()}