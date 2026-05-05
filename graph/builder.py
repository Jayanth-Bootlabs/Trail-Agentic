from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import validate_node, coding_node, unit_tests_node,insights_node,documentation_node

def build_validation_graph():
    graph = StateGraph(GraphState)

    graph.add_node("validate", validate_node)

    graph.set_entry_point("validate")
    graph.add_edge("validate", END)

    return graph.compile()



def build_coding_graph():
    graph = StateGraph(GraphState)

    graph.add_node("coding", coding_node)

    graph.set_entry_point("coding")
    graph.add_edge("coding", END)

    return graph.compile()


def build_unit_tests_graph():
    graph = StateGraph(GraphState)

    graph.add_node("unit_tests", unit_tests_node)

    graph.set_entry_point("unit_tests")
    graph.add_edge("unit_tests", END)

    return graph.compile()


def build_insights_graph():
    graph = StateGraph(GraphState)

    graph.add_node("insights", insights_node)

    graph.set_entry_point("insights")
    graph.add_edge("insights", END)

    return graph.compile()


def build_documentation_graph():
    graph = StateGraph(GraphState)

    graph.add_node("documentation", documentation_node)

    
    graph.set_entry_point("documentation")
    graph.add_edge("documentation", END)

    return graph.compile()