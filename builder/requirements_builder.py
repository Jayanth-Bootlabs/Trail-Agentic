from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.requirements_node import (
    requirements_node,
    retry_node,
)

from graph.transition import (
    requirements_transition,
    retry_transition,
)

from graph.checkpoint import memory


def build_requirements_graph():

    graph = StateGraph(GraphState)

    graph.add_node("requirements", requirements_node)
    graph.add_node("retry_node", retry_node)

    
    graph.set_entry_point("requirements")

    

    graph.add_conditional_edges(
        "requirements",
        requirements_transition,
        {
            "valid": END,
            "retry": "retry_node"
        }
    )

    

    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "requirements",
            "failed": END
        }
    )

    
    return graph.compile(
        checkpointer=memory
    )