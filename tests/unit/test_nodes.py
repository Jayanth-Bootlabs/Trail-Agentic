import asyncio

import pytest

from nodes import (
    code_node as code_module,
    documentation_node as documentation_module,
    insights_node as insights_module,
    requirements_node as requirements_module,
    unit_test_node as unit_test_module,
    validation_node as validation_module,
)


def patch_llm(monkeypatch, module, response="model response", error=None):
    calls = []

    async def generate(prompt, node_name, request_context=None):
        calls.append((prompt, node_name, request_context))
        if error:
            raise error
        return response

    monkeypatch.setattr(module.llm, "generate_for_node", generate)
    monkeypatch.setattr(module, "log_event", lambda **kwargs: None)
    return calls


# Ensures validation returns parsed success while retaining prior state data.
def test_validation_node_sets_valid_status_and_preserves_state(monkeypatch):
    calls = patch_llm(monkeypatch, validation_module)
    monkeypatch.setattr(validation_module, "get_validation_prompt", lambda value: f"prompt:{value}")
    monkeypatch.setattr(
        validation_module,
        "clean_ai_response",
        lambda _: {"status": "valid", "message": "Looks actionable"},
    )
    initial = {"user_input": "Build a task app", "retry_count": 0, "other": "keep"}

    result = asyncio.run(validation_module.validate_node(initial))

    assert result["status"] == "valid"
    assert result["ai_response"]["message"] == "Looks actionable"
    assert result["messages"] == ["Validation completed"]
    assert result["other"] == "keep"
    assert calls[0][2] == "Build a task app"


# Ensures malformed model output enters the graph's retry path.
def test_validation_node_routes_unparseable_response_to_retry(monkeypatch):
    patch_llm(monkeypatch, validation_module)
    monkeypatch.setattr(validation_module, "get_validation_prompt", lambda _: "prompt")
    monkeypatch.setattr(validation_module, "clean_ai_response", lambda _: None)

    result = asyncio.run(validation_module.validate_node({"user_input": "Build an app"}))

    assert result["status"] == "retry"
    assert result["ai_response"]["message"] == "Invalid AI response"


# Verifies safe defaults are applied when the parsed response omits key fields.
def test_validation_node_defaults_missing_status_and_message(monkeypatch):
    patch_llm(monkeypatch, validation_module)
    monkeypatch.setattr(validation_module, "get_validation_prompt", lambda _: "prompt")
    monkeypatch.setattr(validation_module, "clean_ai_response", lambda _: {"extra": "value"})

    result = asyncio.run(validation_module.validate_node({"user_input": "Build an app"}))

    assert result["status"] == "invalid"
    assert result["ai_response"]["message"] == "No response generated"


# Ensures unexpected provider failures remain visible to service-level handlers.
def test_validation_node_reraises_llm_errors(monkeypatch):
    patch_llm(monkeypatch, validation_module, error=RuntimeError("provider offline"))
    monkeypatch.setattr(validation_module, "get_validation_prompt", lambda _: "prompt")

    with pytest.raises(RuntimeError, match="provider offline"):
        asyncio.run(validation_module.validate_node({"user_input": "Build an app"}))


# Confirms provider success labels are normalized to the graph's valid status.
def test_requirements_node_normalizes_success_status(monkeypatch):
    calls = patch_llm(monkeypatch, requirements_module)
    monkeypatch.setattr(requirements_module, "get_requirements_prompt", lambda **kwargs: "requirements prompt")
    monkeypatch.setattr(
        requirements_module,
        "clean_ai_response",
        lambda _: {"status": "success", "data": {"features": ["boards"]}},
    )

    result = asyncio.run(requirements_module.requirements_node({"user_input": "Build a task app"}))

    assert result["status"] == "valid"
    assert result["requirements"]["data"]["features"] == ["boards"]
    assert calls[0][1] == "requirements_node"


# Ensures unparseable requirements output is retried instead of saved as a result.
def test_requirements_node_returns_retry_when_parsing_fails(monkeypatch):
    patch_llm(monkeypatch, requirements_module)
    monkeypatch.setattr(requirements_module, "get_requirements_prompt", lambda **kwargs: "prompt")
    monkeypatch.setattr(requirements_module, "clean_ai_response", lambda _: {})

    result = asyncio.run(requirements_module.requirements_node({"user_input": "Build a task app"}))

    assert result["status"] == "retry"
    assert "requirements" not in result


# Verifies code output and its status are normalized for downstream consumers.
def test_code_node_normalizes_completed_status(monkeypatch):
    patch_llm(monkeypatch, code_module)
    monkeypatch.setattr(code_module, "get_code_prompt", lambda value: f"code:{value}")
    monkeypatch.setattr(code_module, "clean_ai_response", lambda _: {"status": "completed", "source_code": {"main.py": "pass"}})

    result = asyncio.run(code_module.code_node({"user_input": "Make a task app"}))

    assert result["status"] == "valid"
    assert result["code"]["status"] == "valid"
    assert result["code"]["source_code"]["main.py"] == "pass"


# Ensures malformed code output does not create a misleading code artifact.
def test_code_node_returns_retry_for_unparseable_response(monkeypatch):
    patch_llm(monkeypatch, code_module)
    monkeypatch.setattr(code_module, "get_code_prompt", lambda _: "prompt")
    monkeypatch.setattr(code_module, "clean_ai_response", lambda _: None)

    result = asyncio.run(code_module.code_node({"user_input": "Make a task app"}))

    assert result["status"] == "retry"
    assert "code" not in result


# Confirms unit-test output is converted into the schema expected by services.
def test_unit_test_node_builds_test_payload_and_normalizes_status(monkeypatch):
    patch_llm(monkeypatch, unit_test_module)
    monkeypatch.setattr(unit_test_module, "get_unit_tests_prompt", lambda code: "test prompt")
    monkeypatch.setattr(
        unit_test_module,
        "clean_ai_response",
        lambda _: {
            "status": "success",
            "language": "python",
            "framework": "pytest",
            "tests": [{"file_name": "test_app.py", "content": "def test_ok(): pass"}],
        },
    )

    result = asyncio.run(unit_test_module.unit_test_node({"code": {"source_code": {}}}))

    assert result["status"] == "valid"
    assert "# test_app.py\ndef test_ok(): pass" in result["unit_tests"]["test_code"]
    assert result["unit_tests"]["frameworks_used"] == ["pytest"]


# Ensures insights prompts receive requirements, generated code, and test code.
def test_insights_node_passes_all_inputs_to_prompt(monkeypatch):
    patch_llm(monkeypatch, insights_module)
    prompt_args = []
    monkeypatch.setattr(insights_module, "get_insights_prompt", lambda *args: prompt_args.append(args) or "prompt")
    monkeypatch.setattr(insights_module, "clean_ai_response", lambda _: {"status": "valid", "summary": "ok"})
    state = {"requirements": "req", "code": {"main.py": "pass"}, "test_code": "assert True"}

    result = asyncio.run(insights_module.insights_node(state))

    assert prompt_args == [("req", {"main.py": "pass"}, "assert True")]
    assert result["status"] == "valid"
    assert result["insights"]["summary"] == "ok"


# Verifies malformed documentation output requests a retry without adding output.
def test_documentation_node_returns_retry_when_parsing_fails(monkeypatch):
    patch_llm(monkeypatch, documentation_module)
    monkeypatch.setattr(documentation_module, "get_documentation_prompt", lambda *args: "prompt")
    monkeypatch.setattr(documentation_module, "clean_ai_response", lambda _: None)

    result = asyncio.run(
        documentation_module.documentation_node(
            {"requirements": "req", "code": "code", "test_code": "tests"}
        )
    )

    assert result["status"] == "retry"
    assert "documentation" not in result


# Confirms each agent retry node increments its counter and preserves state.
@pytest.mark.parametrize(
    "module",
    [
        validation_module,
        requirements_module,
        code_module,
        unit_test_module,
        insights_module,
        documentation_module,
    ],
)
def test_retry_nodes_increment_retry_count_and_preserve_other_fields(module, monkeypatch):
    monkeypatch.setattr(module, "log_event", lambda **kwargs: None)
    state = {"retry_count": 1, "status": "retry", "messages": ["existing"]}

    result = asyncio.run(getattr(module, "retry_node")(state))

    assert result["retry_count"] == 2
    assert result["status"] == "retry"
    expected_messages = ["existing", "Retry attempt 2"] if module is validation_module else ["existing"]
    assert result["messages"] == expected_messages


# Ensures the validation clarification is carried forward in graph messages.
def test_validation_clarification_node_appends_prompt_to_messages(monkeypatch):
    monkeypatch.setattr(validation_module, "log_event", lambda **kwargs: None)

    result = asyncio.run(
        validation_module.clarification_node(
            {"ai_response": {"message": "Which database?"}, "messages": ["started"]}
        )
    )

    assert result["messages"] == ["started", "Which database?"]


# Verifies rejection still produces a useful message when the model omits one.
def test_validation_rejection_node_uses_default_when_message_missing(monkeypatch):
    monkeypatch.setattr(validation_module, "log_event", lambda **kwargs: None)

    result = asyncio.run(validation_module.rejection_node({"ai_response": {}, "messages": []}))

    assert result["messages"] == ["Request rejected"]
