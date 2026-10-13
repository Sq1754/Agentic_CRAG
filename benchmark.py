import uuid
from src.models import DocumentChunk
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever


def run_benchmark():
    tenant_id = "tenant_alpha"
    retriever = HybridRetriever()
    reranker = CrossEncoderReranker()

    # Ingest a technical test dataset
    docs = [
        "Kubernetes pods can be debugged via ephemeral containers using kubectl debug -it.",
        "Error ERR_SOCKET_TIMEOUT occurs when an upstream HTTP connection exceeds 30000ms in Envoy Proxy.",
        "PostgreSQL pgvector extension supports HNSW and IVF Flat indexes for vector similarity.",
        "Model quantization using AWQ preserves 4-bit weights by protecting salient activation outliers.",
        "The Envoy proxy configuration uses route timeouts to prevent socket hangs during spikes.",
    ]

    chunks = [
        DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id=f"doc_{i}",
            tenant_id=tenant_id,
            content=text,
        )
        for i, text in enumerate(docs)
    ]

    print("[1] Ingesting documents...")
    retriever.index_chunks(tenant_id, chunks)

    query = "How to resolve ERR_SOCKET_TIMEOUT in Envoy?"
    print(f"\n[Query]: {query}\n" + "-" * 50)

    # 1. Naive Dense Only
    dense_hits = retriever.search_dense(tenant_id, query, top_k=3)
    print("\n--- Top Dense Results ---")
    for h in dense_hits:
        print(f"[{h.score:.4f}] {h.content}")

    # 2. Sparse BM25 Only
    sparse_hits = retriever.search_sparse(tenant_id, query, top_k=3)
    print("\n--- Top BM25 Results ---")
    for h in sparse_hits:
        print(f"[{h.score:.4f}] {h.content}")

    # 3. Hybrid RRF
    fused_hits = retriever.reciprocal_rank_fusion(dense_hits, sparse_hits)

    # 4. Cross-Encoder Re-ranking
    reranked = reranker.rerank(query, fused_hits, top_n=2)
    print("\n--- Top Re-ranked Results (Final Retrieval Output) ---")
    for h in reranked:
        print(f"[Calibrated Score: {h.score:.4f}] {h.content}")


if __name__ == "__main__":
    run_benchmark()