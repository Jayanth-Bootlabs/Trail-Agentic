from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import validation_node, requirements_node


def build_validation_graph():
    graph = StateGraph(GraphState)

    graph.add_node("validation", validation_node)

    graph.set_entry_point("validation")
    graph.add_edge("validation", END)

    return graph.compile()


def build_requirements_graph():
    graph = StateGraph(GraphState)

    graph.add_node("requirements", requirements_node)

    graph.set_entry_point("requirements")
    graph.add_edge("requirements", END)

    return graph.compile()