from __future__ import annotations

import json
import re
from typing import Optional


def extract_json_object(text: str) -> Optional[dict]:
    """
    Extract the first valid JSON object from text.

    Handles:
    - Raw JSON strings
    - ```json fenced code blocks
    - JSON embedded inside prose
    """
    if not text or not text.strip():
        return None

    # 1. Try the whole text as JSON
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Try ```json ... ``` or ``` ... ``` fenced blocks
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. Find the first { ... } span (greedy, outermost)
    # Walk character by character to find balanced braces.
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
                break

    return None
