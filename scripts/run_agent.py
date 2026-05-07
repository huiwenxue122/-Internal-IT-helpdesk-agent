"""
scripts/run_agent.py

Thin wrapper around gaggia_agent.main for convenient CLI usage.

Usage:
  python scripts/run_agent.py --message "Can you get David Kim's work email?" \\
      --trust-tier blue --user-id EMP-2200 --show-trace
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gaggia_agent.main import main

if __name__ == "__main__":
    main()
