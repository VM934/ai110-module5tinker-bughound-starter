from reliability.risk_assessor import assess_risk


def test_no_fix_is_high_risk():
    risk = assess_risk(
        original_code="print('hi')\n",
        fixed_code="",
        issues=[{"type": "Code Quality", "severity": "Low", "msg": "print"}],
    )
    assert risk["level"] == "high"
    assert risk["should_autofix"] is False
    assert risk["score"] == 0


def test_low_risk_when_minimal_change_and_low_severity():
    original = "import logging\n\ndef add(a, b):\n    return a + b\n"
    fixed = "import logging\n\ndef add(a, b):\n    return a + b\n"
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[{"type": "Code Quality", "severity": "Low", "msg": "minor"}],
    )
    assert risk["level"] in ("low", "medium")  # depends on scoring rules
    assert 0 <= risk["score"] <= 100


def test_high_severity_issue_drives_score_down():
    original = "def f():\n    try:\n        return 1\n    except:\n        return 0\n"
    fixed = "def f():\n    try:\n        return 1\n    except Exception as e:\n        return 0\n"
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[{"type": "Reliability", "severity": "High", "msg": "bare except"}],
    )
    assert risk["score"] <= 60
    assert risk["level"] in ("medium", "high")


def test_missing_return_is_penalized():
    original = "def f(x):\n    return x + 1\n"
    fixed = "def f(x):\n    x + 1\n"
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[],
    )
    assert risk["score"] < 100
    assert any("Return" in r or "return" in r for r in risk["reasons"])


def test_medium_severity_requires_human_review_even_with_low_risk_score():
    code = "def f():\n    # TODO: improve later\n    return True\n"
    risk = assess_risk(
        original_code=code,
        fixed_code=code,
        issues=[{"type": "Maintainability", "severity": "Medium", "msg": "TODO"}],
    )

    assert risk["level"] == "low"
    assert risk["should_autofix"] is False
    assert any("human review" in reason.lower() for reason in risk["reasons"])


def test_large_rewrite_requires_human_review():
    original = "def greet(name):\n    print('Hello', name)\n    return True\n"
    fixed = (
        "import logging\n\n"
        "def greet(name):\n"
        "    normalized = str(name).strip()\n"
        "    logging.info('Hello %s', normalized)\n"
        "    return bool(normalized)\n"
    )
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[{"type": "Code Quality", "severity": "Low", "msg": "print"}],
    )

    assert risk["level"] == "low"
    assert risk["change_ratio"] > 0.5
    assert risk["should_autofix"] is False
    assert any("human review" in reason.lower() for reason in risk["reasons"])


def test_invalid_python_fix_is_rejected():
    risk = assess_risk(
        original_code="def f():\n    return 1\n",
        fixed_code="def f(:\n    return 1\n",
        issues=[{"type": "Correctness", "severity": "Low", "msg": "example"}],
    )

    assert risk["score"] == 0
    assert risk["level"] == "high"
    assert risk["should_autofix"] is False
    assert any("valid Python" in reason for reason in risk["reasons"])
