# 🐶 BugHound

BugHound is a small agentic debugging system for short Python snippets. It
plans an analysis, detects issues, proposes a minimal fix, evaluates the
change, and then decides whether to allow an automatic fix or require human
review.

This fork completes the AI110 Module 5 Tinker with an emphasis on cautious,
reproducible behavior.

## Agent workflow

1. **Plan** — identify the scan-and-fix workflow.
2. **Analyze** — use deterministic heuristics or Gemini.
3. **Act** — propose a minimal rewrite.
4. **Test** — check severity, syntax, behavior signals, and change size.
5. **Reflect** — auto-fix only when every guardrail allows it.

Gemini is a tool inside the workflow, not the final authority. Invalid JSON,
unknown severity values, unusable code, and API failures all trigger a
deterministic fallback.

## Tinker changes

- **Part 2 — analysis reliability**
  - Rejects any model issue whose severity is not `Low`, `Medium`, or `High`.
  - Rejects a model-generated fix that is not valid Python.
- **Part 3 — safer decision policy**
  - Requires human review for every Medium- or High-severity issue, even if a
    future scoring change leaves the numeric score in the low-risk band.
- **Part 4 — guardrail and tests**
  - Rejects syntactically invalid fixes.
  - Requires human review when a fix changes more than 50% of the content.
  - Adds deterministic tests for invalid severity, invalid Python, the
    severity policy, and over-editing.
- **Part 5 — documentation**
  - Completes `model_card.md` with actual offline evaluation results, failure
    modes, tradeoffs, and human-in-the-loop triggers.

The fork also fixes two starter-level problems: the UI now uses the real
offline agent path instead of a mock LLM path, and a clean virtual environment
can import and run the test suite through `pyproject.toml`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run offline

No key or network connection is required:

```bash
streamlit run bughound_app.py
```

Select **Heuristic only (no API)** in the sidebar.

## Run with Gemini

Create a local environment file and add your own key:

```bash
cp .env.example .env
```

```text
GEMINI_API_KEY=your_real_key_here
```

The `.env` file is ignored by Git and must never be committed. Select
**Gemini (requires API key)** in the app and use the limited free-tier requests
intentionally.

## Tests

```bash
pytest -q
```

Verified result:

```text
.............                                                            [100%]
13 passed in 0.03s
```

The tests cover the workflow shape, heuristic analysis/fixing, parse fallback,
severity-contract fallback, invalid-code fallback, risk scoring, missing
returns, review-required severities, and the large-rewrite guardrail.

## Reproducible offline evaluation

```bash
python evaluate_samples.py
```

```text
| Sample | Issues | Risk | Score | Auto-fix | Change ratio |
|---|---:|---|---:|---|---:|
| cleanish.py | 0 | low | 100 | True | 0.00 |
| flaky_try_except.py | 1 | medium | 55 | False | 0.11 |
| mixed_issues.py | 3 | high | 30 | False | 0.30 |
| print_spam.py | 1 | low | 95 | True | 0.44 |
```

These results show that the low-impact print rewrite can proceed, while the
bare-exception and mixed-issue samples require a person. See
`model_card.md` for the limitations behind those decisions.
