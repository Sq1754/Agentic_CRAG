from sentence_transformers import CrossEncoder
from src.models import SearchResult
import math


class CrossEncoderReranker:
    """Scores (Query, Document) pairs with a joint cross-encoder model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name)

    def rerank(
        self, query: str, candidates: list[SearchResult], top_n: int = 5
    ) -> list[SearchResult]:
        if not candidates:
            return []

        pairs = [[query, candidate.content] for candidate in candidates]
        scores = self.model.predict(pairs)

        for candidate, raw_score in zip(candidates, scores):
            # Sigmoid normalization: map unbounded logits to [0, 1]
            candidate.score = float(1.0 / (1.0 + math.exp(-raw_score)))
            candidate.source = "cross_encoder"

        # Sort descending by re-ranker confidence score
        ranked = sorted(candidates, key=lambda x: x.score, reverse=True)
        return ranked[:top_n]
    