"""
gaggia_agent/main.py

CLI entry point for GaggiaAgent.

Usage:
  python -m gaggia_agent.main --message "Can you get David Kim's work email?" \\
      --trust-tier blue --user-id EMP-2200 --show-trace

  python -m gaggia_agent.main      # runs default smoke test
"""

from __future__ import annotations

import argparse
import json
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaggia_agent",
        description="GaggiaAgent policy-enforcing IT helpdesk.",
    )
    parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Helpdesk request (default: smoke test work-email query).",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="EMP-2200",
        dest="user_id",
        help="Requester employee ID (default: EMP-2200).",
    )
    parser.add_argument(
        "--trust-tier",
        type=str,
        default="blue",
        choices=["blue", "grey", "red"],
        dest="trust_tier",
        help="Trust tier for the requester (default: blue).",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Optional requester profile as a JSON string.",
    )
    parser.add_argument(
        "--show-trace",
        action="store_true",
        dest="show_trace",
        help="Print full routing and policy trace.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    message: str = args.message or "Can you get Sarah Chen's work email?"
    requester_profile = None
    if args.profile:
        try:
            requester_profile = json.loads(args.profile)
        except json.JSONDecodeError as exc:
            print(f"Error: --profile is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    # Lazy import to keep startup fast
    from gaggia_agent.runner import run_agent, summarize_final_state

    state = run_agent(
        user_message=message,
        user_id=args.user_id,
        trust_tier=args.trust_tier,
        requester_profile=requester_profile,
    )
    summary = summarize_final_state(state)

    # ---- Always print ----
    print()
    print("=" * 60)
    print(f"Response:        {summary['response']}")
    print(f"Verdict:         {summary['verdict']}")
    print(f"Cited Sections:  {', '.join(summary['cited_sections']) or '(none)'}")
    print("=" * 60)

    if args.show_trace:
        rm = summary.get("retrieval_metadata") or {}
        print()
        print("── Retrieval Backends ─────────────────────────────────────")
        print(f"  Section backend: {rm.get('section_backend', 'unknown')}")
        if rm.get("section_backend") == "chroma":
            print(f"  Chroma path:     {rm.get('chroma_path', '')}")
            print(f"  Collection:      {rm.get('collection', '')}")
        elif rm.get("fallback_reason"):
            print(f"  Fallback reason: {rm.get('fallback_reason', '')}")
        print(f"  Graph backend:   {rm.get('graph_backend', 'unknown')}")
        print(f"  Neo4j available: {rm.get('neo4j_available', False)}")
        print(f"  Rules loaded:    {rm.get('rules_loaded', 0)}")
        print(f"  Sections returned:        {rm.get('sections_returned', 0)}")
        print(f"  Rules returned:           {rm.get('rules_returned', 0)}")
        print(f"  Graph expanded rules:     {rm.get('graph_expanded_rules_returned', 0)}")
        print("── Routing ────────────────────────────────────────────────")
        print(f"  Intent:          {summary['intent']}")
        print(f"  Requested Fields:{summary['requested_fields']}")
        print(f"  Candidate Tools: {summary['candidate_tools']}")
        print(f"  Retrieved Rules: {summary['retrieved_rule_ids']}")
        if summary["conflicts"]:
            for c in summary["conflicts"]:
                print(f"  Conflict:        {c.get('conflict_type')} "
                      f"{c.get('rule_ids', [])}")
        else:
            print("  Conflicts:       (none)")
        authorized = summary["authorized_tool_calls"]
        if authorized:
            for call in authorized:
                print(f"  Authorized:      {call.get('tool')}({call.get('args', {})})")
        else:
            print("  Authorized:      (none)")
        if summary["blocked_by_guard"]:
            print(f"  Blocked by guard:{summary['blocked_by_guard']}")
        if summary["redacted_fields"]:
            print(f"  Redacted fields: {summary['redacted_fields']}")
        print("───────────────────────────────────────────────────────────")
    print()


if __name__ == "__main__":
    main()
