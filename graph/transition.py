from graph.state import GraphState


def validation_transition(state: GraphState):
    return state.get("status", "invalid")


def requirements_transition(state: GraphState):
    return state.get("status", "invalid")


def code_transition(state: GraphState):
    return state.get("status", "invalid")


def unit_test_transition(state:GraphState):
    return state.get("status","invalid")

def insights_transition(state:GraphState):
    return state.get("status","invalid")

def documentation_transition(state: GraphState):
    return state.get("status", "invalid")


def retry_transition(state: GraphState):
    retry_count = state.get("retry_count", 0)

    if retry_count >= 2:
        return "failed"

    return "retry"