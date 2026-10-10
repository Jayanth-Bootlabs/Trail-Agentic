import pytest

from graph.transition import (
    code_transition,
    documentation_transition,
    insights_transition,
    requirements_transition,
    retry_transition,
    unit_test_transition,
    validation_transition,
)


# Confirms validation outcomes are passed through unchanged for routing.
@pytest.mark.parametrize(
    "status",
    ["valid", "clarify", "invalid", "retry"],
)
def test_validation_transition_returns_status(status):
    assert validation_transition({"status": status}) == status


# Ensures every artifact-stage transition forwards a successful status.
@pytest.mark.parametrize(
    "transition",
    [
        requirements_transition,
        code_transition,
        unit_test_transition,
        insights_transition,
        documentation_transition,
    ],
)
def test_artifact_transition_returns_status(transition):
    assert transition({"status": "valid"}) == "valid"


# Verifies a missing status safely follows the graph's invalid path.
@pytest.mark.parametrize(
    "transition",
    [
        validation_transition,
        requirements_transition,
        code_transition,
        unit_test_transition,
        insights_transition,
        documentation_transition,
    ],
)
def test_stage_transition_defaults_missing_status_to_invalid(transition):
    assert transition({}) == "invalid"


# Checks retries continue below the limit and stop once it is reached.
@pytest.mark.parametrize(
    ("retry_count", "expected"),
    [(0, "retry"), (1, "retry"), (2, "failed"), (3, "failed")],
)
def test_retry_transition_enforces_retry_limit(retry_count, expected):
    assert retry_transition({"retry_count": retry_count}) == expected


# Confirms a missing retry count starts at zero and permits a retry.
def test_retry_transition_defaults_missing_count_to_zero():
    assert retry_transition({}) == "retry"
