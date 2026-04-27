from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import validate_node

def build_validation_graph():
    graph = StateGraph(GraphState)

    graph.add_node("validate", validate_node)

    graph.set_entry_point("validate")
    graph.add_edge("validate", END)

    return graph.compile()