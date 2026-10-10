import asyncio

import pytest

from utils.logger import trace_graph_node


# Ensures the node wrapper logs both incoming and updated graph state.
def test_node_wrapper_logs_state_before_and_after_node(monkeypatch):
    events = []
    monkeypatch.setattr("utils.logger.log_event", lambda **kwargs: events.append(kwargs))

    async def node(state):
        return {**state, "status": "valid", "messages": ["done"]}

    wrapped = trace_graph_node("sample", node)
    result = asyncio.run(wrapped({"user_input": "input", "retry_count": 0}))

    assert result["status"] == "valid"
    assert events[0]["metadata"]["graph_state"]["user_input"] == "input"
    assert events[0]["message"] == "Graph state before node"
    assert events[1]["metadata"]["graph_state"]["status"] == "valid"
    assert events[1]["message"] == "Graph state after node"


# Ensures node exceptions are logged with state context and still propagate.
def test_node_wrapper_logs_error_snapshot_and_reraises(monkeypatch):
    events = []
    monkeypatch.setattr("utils.logger.log_event", lambda **kwargs: events.append(kwargs))

    async def node(_state):
        raise ValueError("bad node input")

    with pytest.raises(ValueError, match="bad node input"):
        asyncio.run(trace_graph_node("sample", node)({"retry_count": 1}))

    error_event = events[-1]
    assert error_event["level"] == "ERROR"
    assert error_event["metadata"]["graph_state"]["error"] == "bad node input"
    assert "ValueError" in error_event["stack_trace"]
