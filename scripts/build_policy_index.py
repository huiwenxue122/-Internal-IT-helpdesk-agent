#!/usr/bin/env python3
"""
Build or rebuild all GaggiaAgent policy indexes.

Usage:
    python scripts/build_policy_index.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gaggia_agent.policy.build_policy_index import build_all_policy_indexes

if __name__ == "__main__":
    print("Building policy indexes...")
    summary = build_all_policy_indexes(reset=True)
    print(f"  sections_indexed : {summary['sections_indexed']}")
    print(f"  rules_loaded     : {summary['rules_loaded']}")
    print(f"  graph_backend    : {summary['graph_backend']}")
    print("Done.")
