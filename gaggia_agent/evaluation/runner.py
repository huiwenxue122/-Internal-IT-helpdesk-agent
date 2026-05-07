"""Run the full evaluation suite over a list of EvalScenarios."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone

from gaggia_agent.evaluation.assertions import evaluate_scenario_result
from gaggia_agent.evaluation.models import EvalResult, EvalScenario
from gaggia_agent.runner import run_agent

_DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "results"
)


def run_evaluation(
    scenarios: list[EvalScenario],
    output_dir: str = _DEFAULT_OUTPUT_DIR,
) -> list[EvalResult]:
    """Run every scenario through the full graph and collect EvalResult objects."""
    os.makedirs(output_dir, exist_ok=True)

    results: list[EvalResult] = []
    for scenario in scenarios:
        try:
            final_state = run_agent(
                user_message=scenario.message,
                user_id=scenario.user_id,
                trust_tier=scenario.trust_tier,
                requester_profile=scenario.requester_profile or None,
            )
        except Exception as exc:  # noqa: BLE001
            # Wrap graph errors so one bad scenario doesn't abort the whole run.
            from gaggia_agent.state import default_state
            final_state = default_state(
                user_message=scenario.message,
                user_id=scenario.user_id,
                trust_tier=scenario.trust_tier,
            )
            final_state["verdict"] = "deny"
            final_state["response"] = f"[ERROR] Graph raised an exception: {exc}"

        result = evaluate_scenario_result(scenario, final_state)
        results.append(result)

    # Write timestamped JSONL (no raw_tool_outputs)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    jsonl_path = os.path.join(output_dir, f"eval_results_{ts}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r.to_dict()) + "\n")

    # Also write / overwrite latest_results.jsonl
    latest_path = os.path.join(output_dir, "latest_results.jsonl")
    shutil.copy(jsonl_path, latest_path)

    return results
