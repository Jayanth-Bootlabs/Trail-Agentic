from langgraph.graph import StateGraph, END

from graph.state import GraphState

from nodes.validation_node import (
    validate_node,
    retry_node,
    clarification_node,
    rejection_node
)

from graph.router import (
    validation_router,
    retry_router
)

from graph.checkpoint import memory


def build_validation_graph():

    graph = StateGraph(GraphState)

    # ---------------- NODES ----------------

    graph.add_node("validate", validate_node)

    graph.add_node("retry_node", retry_node)

    graph.add_node("clarification_node", clarification_node)

    graph.add_node("rejection_node", rejection_node)

    # ---------------- ENTRY ----------------

    graph.set_entry_point("validate")

    # ---------------- VALIDATION ROUTING ----------------

    graph.add_conditional_edges(
        "validate",
        validation_router,
        {
            "valid": END,
            "clarify": "clarification_node",
            "invalid": "rejection_node",
            "retry": "retry_node"
        }
    )

    # ---------------- RETRY ROUTING ----------------

    graph.add_conditional_edges(
        "retry_node",
        retry_router,
        {
            "retry": "validate",
            "failed": "rejection_node"
        }
    )

    # ---------------- END ----------------

    graph.add_edge("clarification_node", END)

    graph.add_edge("rejection_node", END)

    # ---------------- COMPILE ----------------

    return graph.compile(
        checkpointer=memory
    )