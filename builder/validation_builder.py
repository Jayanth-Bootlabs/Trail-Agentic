from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.validation_node import validate_node,retry_node,clarification_node,rejection_node
from graph.transition import validation_transition,retry_transition
from graph.checkpoint import memory


def build_validation_graph():

    graph = StateGraph(GraphState)

    graph.add_node("validate", validate_node)
    graph.add_node("retry_node", retry_node)
    graph.add_node("clarification_node", clarification_node)
    graph.add_node("rejection_node", rejection_node)

    graph.set_entry_point("validate")

    

    graph.add_conditional_edges(
        "validate",
        validation_transition,
        {
            "valid": END,
            "clarify": "clarification_node",
            "invalid": "rejection_node",
            "retry": "retry_node"
        }
    )

    

    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "validate",
            "failed": "rejection_node"
        }
    )

    

    graph.add_edge("clarification_node", END)
    graph.add_edge("rejection_node", END)

    

    return graph.compile(
        checkpointer=memory
    )