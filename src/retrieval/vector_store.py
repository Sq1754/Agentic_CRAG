import math
from typing import List
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src.models import DocumentChunk, SearchResult


class HybridRetriever:
    """Combines Qdrant Dense Vector Search and BM25 Sparse Search with RRF."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "tenant_corpus",
        dense_model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        # Set check_compatibility=False to silence server minor version differences
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port, check_compatibility=False)
        self.collection_name = collection_name
        self.dense_model = SentenceTransformer(dense_model_name)
        # Use get_embedding_dimension instead of the deprecated get_sentence_embedding_dimension
        self.vector_dim = self.dense_model.get_embedding_dimension()

        # In-memory BM25 registry: {tenant_id: (BM25Okapi, list[DocumentChunk])}
        self._bm25_registry: dict[str, tuple[BM25Okapi, list[DocumentChunk]]] = {}

        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the Qdrant collection configured for Cosine distance if not present."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            # Create payload index on tenant_id for sub-millisecond filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="tenant_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )

    def index_chunks(self, tenant_id: str, chunks: list[DocumentChunk]):
        """Indexes chunks into Qdrant (dense) and BM25 index (sparse) under a tenant scope."""
        if not chunks:
            return

        texts = [chunk.content for chunk in chunks]
        embeddings = self.dense_model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )

        # 1. Ingest into Qdrant with tenant payload
        points = [
            qmodels.PointStruct(
                id=hash(chunk.chunk_id) % (2**63 - 1),  # Integer point ID
                vector=embeddings[i].tolist(),
                payload={
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "tenant_id": chunk.tenant_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                },
            )
            for i, chunk in enumerate(chunks)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

        # 2. Build or update tenant BM25 index
        tokenized_corpus = [doc.content.lower().split() for doc in chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        self._bm25_registry[tenant_id] = (bm25, chunks)

    def search_dense(self, tenant_id: str, query: str, top_k: int = 20) -> list[SearchResult]:
        query_vector = self.dense_model.encode(
            query, normalize_embeddings=True
        ).tolist()

        # Enforce strict multi-tenant filtering
        tenant_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="tenant_id",
                    match=qmodels.MatchValue(value=tenant_id),
                )
            ]
        )

        # In modern qdrant-client, use query_points instead of search
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=tenant_filter,
            limit=top_k,
        )

        return [
            SearchResult(
                chunk_id=h.payload["chunk_id"],
                doc_id=h.payload["doc_id"],
                content=h.payload["content"],
                score=float(h.score),
                source="dense",
                metadata=h.payload.get("metadata", {}),
            )
            for h in response.points
        ]

    def search_sparse(self, tenant_id: str, query: str, top_k: int = 20) -> list[SearchResult]:
        if tenant_id not in self._bm25_registry:
            return []

        bm25, chunks = self._bm25_registry[tenant_id]
        tokens = query.lower().split()
        scores = bm25.get_scores(tokens)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue
            chunk = chunks[idx]
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=score,
                    source="sparse",
                    metadata=chunk.metadata,
                )
            )
        return results

    @staticmethod
    def reciprocal_rank_fusion(
        dense_results: list[SearchResult],
        sparse_results: list[SearchResult],
        k: int = 60,
    ) -> list[SearchResult]:
        """Merges two ranked lists using Reciprocal Rank Fusion (RRF).

        Score(d) = sum(1 / (k + rank_i))
        """
        rrf_scores: dict[str, float] = {}
        lookup: dict[str, SearchResult] = {}

        # Process dense ranks
        for rank, res in enumerate(dense_results):
            rrf_scores[res.chunk_id] = rrf_scores.get(res.chunk_id, 0.0) + (
                1.0 / (k + rank + 1)
            )
            lookup[res.chunk_id] = res

        # Process sparse ranks
        for rank, res in enumerate(sparse_results):
            rrf_scores[res.chunk_id] = rrf_scores.get(res.chunk_id, 0.0) + (
                1.0 / (k + rank + 1)
            )
            if res.chunk_id not in lookup:
                lookup[res.chunk_id] = res

        # Sort combined results by RRF score descending
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        merged = []
        for chunk_id, fused_score in sorted_chunks:
            item = lookup[chunk_id]
            merged.append(
                SearchResult(
                    chunk_id=item.chunk_id,
                    doc_id=item.doc_id,
                    content=item.content,
                    score=fused_score,
                    source="rrf_hybrid",
                    metadata=item.metadata,
                )
            )
        return merged