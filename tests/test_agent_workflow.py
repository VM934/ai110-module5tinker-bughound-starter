from bughound_agent import BugHoundAgent
from llm_client import MockClient


class InvalidSeverityClient:
    """Return valid JSON whose severity violates the analyzer contract."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return '[{"type":"Reliability","severity":"Critical","msg":"bad value"}]'


class InvalidFixClient:
    """Return valid analysis followed by an invalid Python rewrite."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if "Return ONLY valid JSON" in system_prompt:
            return '[{"type":"Code Quality","severity":"Low","msg":"print call"}]'
        return "def broken(:\n    pass"


def test_workflow_runs_in_offline_mode_and_returns_shape():
    agent = BugHoundAgent(client=None)  # heuristic-only
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert isinstance(result, dict)
    assert "issues" in result
    assert "fixed_code" in result
    assert "risk" in result
    assert "logs" in result

    assert isinstance(result["issues"], list)
    assert isinstance(result["fixed_code"], str)
    assert isinstance(result["risk"], dict)
    assert isinstance(result["logs"], list)
    assert len(result["logs"]) > 0


def test_offline_mode_detects_print_issue():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])


def test_offline_mode_proposes_logging_fix_for_print():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    fixed = result["fixed_code"]
    assert "logging" in fixed
    assert "logging.info(" in fixed


def test_mock_client_forces_llm_fallback_to_heuristics_for_analysis():
    # MockClient returns non-JSON for analyzer prompts, so agent should fall back.
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])
    # Ensure we logged the fallback path
    assert any("Falling back to heuristics" in entry.get("message", "") for entry in result["logs"])


def test_invalid_severity_forces_heuristic_fallback():
    agent = BugHoundAgent(client=InvalidSeverityClient())
    code = "def f():\n    print('hi')\n"

    result = agent.run(code)

    assert result["issues"] == [
        {
            "type": "Code Quality",
            "severity": "Low",
            "msg": "Found print statements. Consider using logging for non-toy code.",
        }
    ]
    assert any(
        "invalid severity" in entry.get("message", "").lower()
        for entry in result["logs"]
    )


def test_invalid_python_fix_forces_heuristic_fallback():
    agent = BugHoundAgent(client=InvalidFixClient())
    code = "def f():\n    print('hi')\n"

    result = agent.run(code)

    compile(result["fixed_code"], "<test-fix>", "exec")
    assert "logging.info(" in result["fixed_code"]
    assert any(
        "invalid python" in entry.get("message", "").lower()
        for entry in result["logs"]
    )
