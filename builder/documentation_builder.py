from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.documentation_node import documentation_node,retry_node
from graph.transition import documentation_transition,retry_transition
from graph.checkpoint import memory


def build_documentation_graph():

    graph = StateGraph(GraphState)

    graph.add_node("documentation", documentation_node)
    graph.add_node("retry_node", retry_node)

    graph.set_entry_point("documentation")

    graph.add_conditional_edges(
        "documentation",
        documentation_transition,
        {
            "valid": END,
            "retry": "retry_node"
        }
    )

    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "documentation",
            "failed": END
        }
    )

    

    return graph.compile(
        checkpointer=memory
    )