from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.unit_test_node import unit_test_node,retry_node
from graph.transition import unit_test_transition,retry_transition

from graph.checkpoint import memory
from utils.logger import trace_graph_node


def build_unit_test_graph():

    graph = StateGraph(GraphState)

    graph.add_node("unit_test", trace_graph_node("unit_test", unit_test_node))
    graph.add_node("retry_node", trace_graph_node("retry_node", retry_node))

    graph.set_entry_point("unit_test")



    graph.add_conditional_edges(
        "unit_test",
        unit_test_transition,
        {
            "valid": END,
            "retry": "retry_node"
        }
    )

    

    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "unit_test",
            "failed": END
        }
    )


    return graph.compile(
        checkpointer=memory
    )
