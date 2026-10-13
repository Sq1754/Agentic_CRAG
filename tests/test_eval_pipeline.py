import asyncio
import hashlib
import json
import os
import time
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from groq import RateLimitError
from langchain_groq import ChatGroq

from src.config import settings
from src.graph.nodes import CRAGNodes
from src.graph.workflow import build_crag_graph
from src.models import DocumentChunk
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever

BENCHMARK_CORPUS = [
    "Database connection pooling is handled by PgBouncer configured in transaction mode.",
    "Max client connections are capped at 5000 with a default pool size of 20 per database user.",
]


class GroqEvalLLM(DeepEvalBaseLLM):
    """Custom DeepEval evaluator model with automatic rate-limit backoff."""

    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        self.model_name = model_name
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.0,
            api_key=os.environ["GROQ_API_KEY"],
        )

    def load_model(self):
        return self.llm

    def generate(self, prompt: str) -> str:
        for attempt in range(5):
            try:
                res = self.llm.invoke(prompt)
                return str(res.content)
            except RateLimitError:
                sleep_sec = 2 * (attempt + 1)
                print(f"\n[RateLimit on generate] Backing off for {sleep_sec}s...")
                time.sleep(sleep_sec)
        res = self.llm.invoke(prompt)
        return str(res.content)

    async def a_generate(self, prompt: str) -> str:
        for attempt in range(5):
            try:
                res = await self.llm.ainvoke(prompt)
                return str(res.content)
            except RateLimitError:
                sleep_sec = 2 * (attempt + 1)
                print(f"\n[RateLimit on a_generate] Backing off for {sleep_sec}s...")
                await asyncio.sleep(sleep_sec)
        res = await self.llm.ainvoke(prompt)
        return str(res.content)

    def get_model_name(self) -> str:
        return self.model_name


@pytest.fixture(scope="session")
def eval_llm():
    return GroqEvalLLM(model_name=settings.groq_model)


@pytest.fixture(scope="session")
def retriever():
    """Initializes and seeds the retriever once per test session."""
    r = HybridRetriever(
        qdrant_host=settings.qdrant_host,
        qdrant_port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
        dense_model_name=settings.dense_model,
    )
    tenant_id = "team_infra"
    chunks = [
        DocumentChunk(
            chunk_id=hashlib.sha256(f"{tenant_id}_{doc}".encode()).hexdigest()[:16],
            doc_id=f"doc_{i}",
            tenant_id=tenant_id,
            content=doc,
        )
        for i, doc in enumerate(BENCHMARK_CORPUS)
    ]
    r.index_chunks(tenant_id, chunks)
    return r


@pytest.fixture(scope="session")
def pipeline(retriever):
    """Builds the CRAG graph using the seeded retriever."""
    reranker = CrossEncoderReranker(model_name=settings.reranker_model)
    nodes = CRAGNodes(
        retriever=retriever,
        reranker=reranker,
        model_name=settings.groq_model,
    )
    return build_crag_graph(nodes)


def load_golden_cases():
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", load_golden_cases())
def test_crag_quality_gate(pipeline, eval_llm, case):
    """Quality Gate: Evaluates faithfulness and answer relevancy against golden set."""
    state = {
        "query": case["query"],
        "rewritten_query": "",
        "tenant_id": case["tenant_id"],
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": 2,
    }

    final_state = pipeline.invoke(state)
    actual_output = final_state.get("generation", "")
    retrieval_contexts = [d.content for d in final_state.get("documents", [])]

    assert len(retrieval_contexts) > 0, f"No documents retrieved for query: {case['query']}"
    assert any(
        case["context_expected_snippet"] in c for c in retrieval_contexts
    ), f"Expected snippet '{case['context_expected_snippet']}' not found in: {retrieval_contexts}"

    test_case = LLMTestCase(
        input=case["query"],
        actual_output=actual_output,
        expected_output=case["ground_truth"],
        retrieval_context=retrieval_contexts,
    )

    faithfulness_metric = FaithfulnessMetric(threshold=0.7, model=eval_llm)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=eval_llm)

    assert_test(test_case, [faithfulness_metric, relevancy_metric])

    # Cooldown buffer to avoid rate-limiting between test cases
    time.sleep(4)