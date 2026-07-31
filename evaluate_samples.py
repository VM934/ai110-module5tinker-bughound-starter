"""Run a deterministic, offline evaluation of BugHound's sample snippets."""

from pathlib import Path

from bughound_agent import BugHoundAgent


SAMPLE_DIR = Path(__file__).parent / "sample_code"


def main() -> None:
    """Print a parseable summary for each bundled sample."""
    print("| Sample | Issues | Risk | Score | Auto-fix | Change ratio |")
    print("|---|---:|---|---:|---|---:|")

    for path in sorted(SAMPLE_DIR.glob("*.py")):
        result = BugHoundAgent(client=None).run(path.read_text(encoding="utf-8"))
        risk = result["risk"]
        print(
            f"| {path.name} | {len(result['issues'])} | {risk['level']} | "
            f"{risk['score']} | {risk['should_autofix']} | "
            f"{risk.get('change_ratio', 0):.2f} |"
        )


if __name__ == "__main__":
    main()
