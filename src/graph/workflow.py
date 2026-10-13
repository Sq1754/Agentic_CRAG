from langgraph.graph import END, START, StateGraph

from src.graph.nodes import CRAGNodes
from src.graph.state import GraphState


def route_after_grading(state: GraphState) -> str:
    """Conditional Edge: Routes based on document grading & retry count."""
    relevance_status = state["relevance_status"]
    loop_count = state.get("loop_count", 0)
    max_retries = state.get("max_retries", 2)

    if relevance_status == "relevant":
        return "generate"

    # Context is insufficient: check retry budget
    if loop_count < max_retries:
        return "rewrite_query"
    else:
        return "fallback_search"


def route_after_generation(state: GraphState, nodes: CRAGNodes) -> str:
    """Conditional Edge: Validates answer groundedness (hallucination check)."""
    generation = state["generation"]
    docs = state["documents"]
    context_str = "\n".join([d.content for d in docs])

    # If already using fallback context, exit directly
    if state.get("relevance_status") == "fallback":
        return END

    try:
        check = nodes.hallucination_grader.invoke(
            f"Context: {context_str}\n\nStudent Answer: {generation}"
        )
        if check.binary_score.lower() == "yes":
            return END
    except Exception:
        return END

    # If hallucinated and budget allows, rewrite and try again
    loop_count = state.get("loop_count", 0)
    max_retries = state.get("max_retries", 2)

    if loop_count < max_retries:
        return "rewrite_query"
    return END


def build_crag_graph(nodes: CRAGNodes):
    workflow = StateGraph(GraphState)

    # 1. Add Nodes
    workflow.add_node("retrieve", nodes.retrieve)
    workflow.add_node("grade_documents", nodes.grade_documents)
    workflow.add_node("rewrite_query", nodes.rewrite_query)
    workflow.add_node("fallback_search", nodes.fallback_search)
    workflow.add_node("generate", nodes.generate)

    # 2. Add Edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    # Conditional routing after grading
    workflow.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "generate": "generate",
            "rewrite_query": "rewrite_query",
            "fallback_search": "fallback_search",
        },
    )

    # From rewrite, re-run retrieval
    workflow.add_edge("rewrite_query", "retrieve")

    # From fallback search, proceed directly to generation
    workflow.add_edge("fallback_search", "generate")

    # Conditional check after generation
    workflow.add_conditional_edges(
        "generate",
        lambda state: route_after_generation(state, nodes),
        {
            END: END,
            "rewrite_query": "rewrite_query",
        },
    )

    return workflow.compile()