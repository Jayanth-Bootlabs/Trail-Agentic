from graph.state import GraphState


def validation_router(state: GraphState):
    return state.get("status", "invalid")


def retry_router(state: GraphState):
    retry_count = state.get("retry_count", 0)

    if retry_count >= 2:
        return "failed"

    return "retry"