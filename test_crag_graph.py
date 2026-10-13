import os
from src.graph.nodes import CRAGNodes
from src.graph.workflow import build_crag_graph
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever


def run_pipeline_test():
    retriever = HybridRetriever()
    reranker = CrossEncoderReranker()

    # Uses the free Groq model
    nodes = CRAGNodes(
        retriever=retriever,
        reranker=reranker,
        model_name="openai/gpt-oss-20b",
    )
    app = build_crag_graph(nodes)

    print("=" * 60)
    print("TEST 1: In-Domain Query (Direct Retrieval & Answer)")
    print("=" * 60)
    initial_state_1 = {
        "query": "What causes ERR_SOCKET_TIMEOUT in Envoy?",
        "rewritten_query": "",
        "tenant_id": "tenant_alpha",
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": 2,
    }

    for output in app.stream(initial_state_1):
        for node_name, state_update in output.items():
            print(f"--> Finished Node: [{node_name}]")
            if "generation" in state_update:
                print(f"\nFinal Generation:\n{state_update['generation']}")

    print("\n" + "=" * 60)
    print("TEST 2: Out-of-Domain Query (Triggers Retry Loop -> Live DDG Fallback)")
    print("=" * 60)
    initial_state_2 = {
        "query": "How do I bake sourdough bread?",
        "rewritten_query": "",
        "tenant_id": "tenant_alpha",
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": 2,
    }

    for output in app.stream(initial_state_2):
        for node_name, state_update in output.items():
            print(f"--> Finished Node: [{node_name}]")
            if "loop_count" in state_update:
                print(f"    Rewrite Attempt: {state_update['loop_count']}")
            if "generation" in state_update:
                print(f"\nFinal Generation:\n{state_update['generation']}")


if __name__ == "__main__":
    run_pipeline_test()