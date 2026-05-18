from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.insights_node import insights_node, retry_node
from graph.transition import insights_transition, retry_transition
from graph.checkpoint import memory


def build_insights_graph():

    graph = StateGraph(GraphState)

    graph.add_node("insights", insights_node)
    graph.add_node("retry_node", retry_node)

    graph.set_entry_point("insights")

    graph.add_conditional_edges(
        "insights",
        insights_transition,
        {
            "valid": END,
            "retry": "retry_node"
        }
    )

    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "insights",
            "failed": END
        }
    )

    return graph.compile(checkpointer=memory)