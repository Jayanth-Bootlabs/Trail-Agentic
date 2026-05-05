from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import validate_node, requirements_node, coding_node

def build_validation_graph():
    graph = StateGraph(GraphState)

    graph.add_node("validate", validate_node)

    graph.set_entry_point("validate")
    graph.add_edge("validate", END)

    return graph.compile()


def build_requirements_graph():
    graph = StateGraph(GraphState)

    graph.add_node("requirements", requirements_node)

    graph.set_entry_point("requirements")
    graph.add_edge("requirements", END)

    return graph.compile()

def build_coding_graph():
    graph = StateGraph(GraphState)

    graph.add_node("coding", coding_node)

    graph.set_entry_point("coding")
    graph.add_edge("coding", END)

    return graph.compile()