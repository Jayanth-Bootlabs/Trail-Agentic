from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import validation_node, requirements_node,insights_node,documentation_node


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


def build_insights_graph():
    graph=StateGraph(GraphState)

    graph.add_node("insights",insights_node)

    graph.set_entry_point("insights")
    graph.add_edge("insights",END)

    return graph.compile()

def build_documentation_graph():
    graph=StateGraph(GraphState)

    graph.add_node("documents",documentation_node)

    graph.set_entry_point("documents")
    graph.add_edge("documents",END)

    return graph.compile()