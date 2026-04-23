from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import llm_node

def build_graph():
    graph = StateGraph(GraphState)

    # Only one node
    graph.add_node("llm", llm_node)

    # Entry point directly to LLM
    graph.set_entry_point("llm")

    # End after LLM
    graph.add_edge("llm", END)

    return graph.compile()