from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import start_node, llm_node, end_node


def build_graph():
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("start", start_node)
    graph.add_node("llm", llm_node)
    graph.add_node("end", end_node)

    # Define flow (edges)
    graph.set_entry_point("start")

    graph.add_edge("start", "llm")
    graph.add_edge("llm", "end")
    graph.add_edge("end", END)

    return graph.compile()