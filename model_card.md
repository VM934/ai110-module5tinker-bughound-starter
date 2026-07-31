# BugHound Mini Model Card

## 1. System overview

**Name:** BugHound

**Core purpose:** BugHound analyzes a short Python snippet, drafts a targeted
fix, evaluates the risk of that change, and decides whether the result can be
auto-fixed or needs human review.

**Intended users:** Students and early-career developers learning how agentic
workflows, model integration, tests, and guardrails fit together. It is a
learning tool, not a production code-review or security scanner.

## 2. Workflow

BugHound runs a five-step loop:

1. **Plan:** record the intended scan-and-fix process.
2. **Analyze:** use three deterministic patterns in offline mode or ask Gemini
   for a JSON list of issues.
3. **Act:** use the local fixer or ask Gemini for a full rewritten snippet.
4. **Test:** score severity and inspect structural risks, Python syntax,
   missing returns, and the size of the change.
5. **Reflect:** allow an auto-fix only if the risk policy and all hard
   guardrails agree.

The heuristic analyzer recognizes `print(`, bare `except:`, and `TODO`.
Gemini mode sends prompt templates from `prompts/` to the model. If a model
call fails, the response is not valid JSON, a severity is outside the contract,
or a proposed fix is not valid Python, BugHound falls back to deterministic
behavior. The model can suggest; the code makes the trust decision.

## 3. Inputs and outputs

I ran the deterministic evaluation with:

```bash
python evaluate_samples.py
```

| Input | Shape | Issues | Risk | Score | Auto-fix |
|---|---|---:|---|---:|---|
| `cleanish.py` | Function using logging | 0 | low | 100 | yes; no change |
| `flaky_try_except.py` | File read in a bare try/except | 1 | medium | 55 | no |
| `mixed_issues.py` | TODO, print, division, bare except | 3 | high | 30 | no |
| `print_spam.py` | Small function with two prints | 1 | low | 95 | yes |

Outputs include a structured issue list, full proposed code, a unified diff in
the UI, a risk report, the auto-fix decision, and a trace for every workflow
stage.

## 4. Reliability and safety rules

### Missing-return rule

- **Check:** subtract 30 points if the original contains `return` and the fix
  does not.
- **Why it matters:** removing a return frequently changes a function’s public
  behavior.
- **Possible false positive:** a correct refactor might move the return into a
  helper and still preserve behavior.
- **Possible false negative:** a fix can retain the word `return` while
  returning the wrong value.

### Severity rule

- **Check:** Low, Medium, and High issues deduct 5, 20, and 40 points.
  Medium or High also forces human review.
- **Why it matters:** a serious or ambiguous issue should not be silently
  rewritten merely because the aggregate score looks acceptable.
- **Possible false positive:** a deliberately broad exception at an application
  boundary may be labeled High even when it is intentional.
- **Possible false negative:** an important logic bug that neither analyzer
  detects receives no severity at all.

### Syntax and change-size guardrails

- Proposed code that does not compile is always High risk and never auto-fixed.
- A change ratio above 50% requires human review even if the score remains in
  the low-risk band.

The size rule may flag a safe formatting change, but that is an acceptable
false positive for a cautious teaching tool. It can still miss a dangerous
one-line semantic change, so it is not a substitute for tests or review.

## 5. Observed failure modes

### Missed issue

The offline analyzer does not flag this overly broad handler because it only
recognizes a *bare* `except:`:

```python
try:
    load_data()
except Exception:
    return None
```

That means the system can miss swallowed errors even though they have the same
operational effect as the pattern it recognizes.

### Unnecessary or risky edit

A string or comment containing the literal text `print(` can trigger the
simple substring heuristic even when there is no function call. The fixer also
uses a direct text replacement, so it can alter that string. The change-size
guardrail reduces the chance of auto-applying a large version of this error,
but the detection itself still needs a future token- or AST-aware improvement.

### Model-format failure

An LLM can return readable prose, valid JSON with an unsupported severity such
as `Critical`, or syntactically broken code. The test suite reproduces all
three cases without spending API quota and verifies that BugHound falls back or
refuses to auto-fix.

## 6. Heuristic and Gemini comparison

The heuristic path was run directly and is deterministic: it consistently
finds its three known patterns and produces predictable edits. Its main
weakness is narrow coverage.

No Gemini API key was stored on this computer, so I did **not** invent a live
Gemini result. Instead, the Gemini integration boundary was exercised with
deterministic test clients:

- malformed analysis text causes heuristic fallback;
- valid JSON with invalid severity causes heuristic fallback;
- invalid Python from the fixer causes heuristic fallback.

A live Gemini run may find more contextual issues and draft more natural
repairs, but it can also over-edit or violate the output contract. That
model-quality comparison remains unverified until the user supplies a private
Gemini key; the safety behavior around those responses is already tested.

## 7. Human-in-the-loop decision

BugHound must refuse to auto-fix when a proposal changes more than half of the
snippet, contains invalid Python, removes a return, or addresses any Medium- or
High-severity issue.

The triggers belong in `reliability/risk_assessor.py` because that module is the
single policy layer shared by offline and Gemini modes. The UI should show:

> Human review required: the proposed fix is too large, invalid, or addresses
> a non-trivial issue. Review the diff and run project-specific tests before
> applying it.

## 8. Low-complexity improvement

Replace substring detection and replacement for `print(` with Python’s
`tokenize` or `ast` module. That would distinguish real calls from examples in
strings and comments without adding another model call or making the workflow
much more complex. A focused regression test should prove that
`message = "call print(x)"` remains unchanged while a real `print(x)` is still
detected.
