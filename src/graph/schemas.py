from pydantic import BaseModel, Field


class DocumentRelevance(BaseModel):
    """Binary score for document relevance check."""

    binary_score: str = Field(
        description="Relevance check: 'yes' if document contains relevant keywords/facts, 'no' otherwise."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")


class HallucinationGrade(BaseModel):
    """Binary score for checking whether the response is grounded in facts."""

    binary_score: str = Field(
        description="Grounded check: 'yes' if the answer is grounded in facts, 'no' otherwise."
    )
    reasoning: str = Field(description="Explanation of any unsupported claims found.")


class AnswerRelevance(BaseModel):
    """Binary score for checking whether the response actually answers the query."""

    binary_score: str = Field(
        description="Relevance check: 'yes' if the answer addresses the user query, 'no' otherwise."
    )