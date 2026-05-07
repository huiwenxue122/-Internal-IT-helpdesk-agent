"""Generate a human-readable Markdown evaluation report."""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

from gaggia_agent.evaluation.models import EvalResult

_DEFAULT_OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "results", "eval_report.md"
)

_KNOWN_LIMITATIONS = [
    (
        "Deterministic fallbacks",
        "Local fallback heuristics are rule-based and may be less flexible than a live LLM. "
        "Edge-case phrasing can produce unexpected verdicts.",
    ),
    (
        "Red general policy questions",
        "Team Red users cannot call tools (§1.2), so general HR policy questions that require "
        "`query_hr_database` are conservatively denied or escalated rather than answered.",
    ),
    (
        "Neo4j optional",
        "Policy graph uses the in-memory fallback locally when Neo4j credentials are absent. "
        "Graph traversal depth is limited compared to the full AuraDB deployment.",
    ),
    (
        "Mock tools",
        "All tool side-effects are simulated with fake data. The evaluation measures "
        "policy enforcement behavior, not real IT actions.",
    ),
    (
        "Grey cross-team drive access",
        "Grey users requesting cross-team drives without explicit team membership or duration "
        "receive a 'clarify' verdict. The system asks for business justification before "
        "allowing access per §4.2.",
    ),
]


def _pass_icon(passed: bool) -> str:
    return "✅" if passed else "❌"


def write_markdown_report(
    results: list[EvalResult],
    output_path: str = _DEFAULT_OUTPUT_PATH,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0.0

    # Group by category
    by_category: dict[str, list[EvalResult]] = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)

    lines: list[str] = []

    lines.append("# GaggiaAgent Evaluation Report\n")
    lines.append(f"## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total scenarios | {total} |")
    lines.append(f"| Passed | {passed} |")
    lines.append(f"| Failed | {failed} |")
    lines.append(f"| Pass rate | {pass_rate:.1f}% |\n")

    lines.append("## Results by Category\n")
    for category in sorted(by_category):
        cat_results = by_category[category]
        cat_pass = sum(1 for r in cat_results if r.passed)
        cat_total = len(cat_results)
        lines.append(f"### {category} ({cat_pass}/{cat_total})\n")

    lines.append("## Detailed Results\n")
    lines.append(
        "| ID | Name | Category | Pass | Verdict | Citations | Authorized Tools | Failures |"
    )
    lines.append("|-----|------|----------|------|---------|-----------|-----------------|----------|")

    for r in results:
        icon = _pass_icon(r.passed)
        citations = ", ".join(r.cited_sections[:5]) or "—"
        tools = ", ".join(r.authorized_tools) or "—"
        failure_summary = "; ".join(r.failures[:2]) if r.failures else "—"
        # Escape pipe characters for Markdown table safety
        failure_summary = failure_summary.replace("|", "\\|")
        name_short = r.name[:40]
        lines.append(
            f"| {r.scenario_id} | {name_short} | {r.category} | {icon} "
            f"| {r.verdict} | {citations} | {tools} | {failure_summary} |"
        )

    lines.append("\n## Failure Analysis\n")
    failing = [r for r in results if not r.passed]
    if not failing:
        lines.append("All scenarios passed.\n")
    else:
        for r in failing:
            lines.append(f"### {r.scenario_id}: {r.name}\n")
            lines.append(f"**Verdict**: `{r.verdict}`  ")
            lines.append(f"**Category**: {r.category}\n")
            lines.append("**Failures:**\n")
            for f in r.failures:
                lines.append(f"- {f}")
            lines.append("")

    lines.append("\n## Known Limitations\n")
    for title, desc in _KNOWN_LIMITATIONS:
        lines.append(f"**{title}**: {desc}\n")

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
