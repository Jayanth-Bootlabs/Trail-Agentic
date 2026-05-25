from langgraph.graph import StateGraph, END
from graph.state import GraphState

from nodes.code_node import code_node,retry_node
from graph.transition import code_transition,retry_transition

from graph.checkpoint import memory


def build_code_graph():

    graph = StateGraph(GraphState)

    graph.add_node("code", code_node)
    graph.add_node("retry_node", retry_node)

    graph.set_entry_point("code")

    

    graph.add_conditional_edges(
        "code",
        code_transition,
        {
            "valid": END,
            "retry": "retry_node"
        }
    )


    graph.add_conditional_edges(
        "retry_node",
        retry_transition,
        {
            "retry": "code",
            "failed": END
        }
    )

    
    return graph.compile(
        checkpointer=memory
    )