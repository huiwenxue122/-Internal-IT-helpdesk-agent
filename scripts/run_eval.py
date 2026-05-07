#!/usr/bin/env python3
"""CLI for running the GaggiaAgent evaluation suite (Phase 5)."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gaggia_agent.evaluation.report import write_markdown_report
from gaggia_agent.evaluation.runner import run_evaluation
from gaggia_agent.evaluation.scenario_loader import (
    _GENERATED_YAML,
    _OFFICIAL_YAML,
    load_scenarios,
)

_DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gaggia_agent", "evaluation", "results",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run GaggiaAgent evaluation suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_eval.py --all
  python scripts/run_eval.py --official-only
  python scripts/run_eval.py --generated-only --output-dir /tmp/eval
""",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--official-only", action="store_true", help="Run only the 21 official scenarios")
    mode.add_argument("--generated-only", action="store_true", help="Run only generated scenarios")
    mode.add_argument("--all", action="store_true", default=True, help="Run all scenarios (default)")
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Directory for JSONL and Markdown output (default: {_DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    scenarios = []
    if args.official_only:
        if os.path.exists(_OFFICIAL_YAML):
            scenarios = load_scenarios(_OFFICIAL_YAML)
        else:
            print(f"[WARN] Official scenarios file not found: {_OFFICIAL_YAML}")
    elif args.generated_only:
        if os.path.exists(_GENERATED_YAML):
            scenarios = load_scenarios(_GENERATED_YAML)
        else:
            print(f"[WARN] Generated scenarios file not found: {_GENERATED_YAML}")
    else:  # --all (default)
        if os.path.exists(_OFFICIAL_YAML):
            scenarios.extend(load_scenarios(_OFFICIAL_YAML))
        if os.path.exists(_GENERATED_YAML):
            scenarios.extend(load_scenarios(_GENERATED_YAML))

    if not scenarios:
        print("[ERROR] No scenarios loaded. Check that YAML files exist.")
        sys.exit(1)

    print(f"Running evaluation on {len(scenarios)} scenario(s)...")

    results = run_evaluation(scenarios, output_dir=args.output_dir)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0.0

    report_path = os.path.join(args.output_dir, "eval_report.md")
    write_markdown_report(results, output_path=report_path)

    import json
    latest_path = os.path.join(args.output_dir, "latest_results.jsonl")

    print()
    print("=" * 60)
    print(f"  GaggiaAgent Evaluation Results")
    print("=" * 60)
    print(f"  Total    : {total}")
    print(f"  Passed   : {passed}")
    print(f"  Failed   : {failed}")
    print(f"  Pass rate: {pass_rate:.1f}%")
    print()
    print(f"  Report   : {report_path}")
    print(f"  JSONL    : {latest_path}")
    print("=" * 60)

    if failed:
        print("\nFailed scenarios:")
        for r in results:
            if not r.passed:
                print(f"  [{r.scenario_id}] {r.name}")
                for f in r.failures[:3]:
                    print(f"      • {f}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
