from __future__ import annotations

import os
import re
from typing import List, Optional

from gaggia_agent.policy.models import PolicySection

_POLICY_PATH = os.path.join(os.path.dirname(__file__), "gaggia_it_helpdesk_policy_expanded.md")

_HEADING_RE = re.compile(r"^(#{2,3})\s+(\d+(?:\.\d+)*)\.?\s+(.+)$")

_DOMAIN_MAP: dict[str, str] = {
    "0": "general",
    "1": "trust_tier",
    "2": "account_management",
    "3": "directory",
    "4": "file_access",
    "5": "hr_data",
    "6": "escalation",
    "7": "general_conduct",
    "8": "acceptable_use",
    "9": "data_classification",
    "10": "device_support",
    "11": "remote_access",
    "12": "software",
    "13": "privileged_access",
    "14": "incident_reporting",
    "15": "legal_compliance",
    "16": "vendor_access",
    "17": "approvals",
    "18": "multi_turn",
    "19": "tool_use",
    "20": "monitoring",
    "21": "quick_reference",
    "22": "examples",
    "23": "glossary",
}

_TAG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"salary|compensation|bonus"), "compensation"),
    (re.compile(r"performance"), "performance"),
    (re.compile(r"disciplinary"), "disciplinary"),
    (re.compile(r"employment status|active status|currently active"), "employment_status"),
    (re.compile(r"personal email|personal phone|home address"), "personal_contact"),
    (re.compile(r"work email|work phone"), "work_contact"),
    (re.compile(r"legal.hold|legal hold"), "legal_hold"),
    (re.compile(r"restricted drive|restricted"), "restricted"),
    (re.compile(r"personal drive"), "personal_drive"),
    (re.compile(r"service account"), "service_account"),
    (re.compile(r"\badmin\b"), "admin_account"),
    (re.compile(r"\bexecutive\b"), "executive_account"),
    (re.compile(r"team red"), "team_red"),
    (re.compile(r"team grey"), "team_grey"),
    (re.compile(r"team blue"), "team_blue"),
    (re.compile(r"\bescalate\b"), "escalation"),
    (re.compile(r"prompt injection|ignore your instructions"), "prompt_injection"),
    (re.compile(r"raw tool output|\bfilter\b"), "output_filtering"),
]


def _infer_domain(section_id: str) -> str:
    top = section_id.split(".")[0]
    return _DOMAIN_MAP.get(top, "general")


def _infer_modality(content: str) -> Optional[str]:
    lower = content.lower()
    if "must not" in lower:
        return "must_not"
    if "must" in lower:
        return "must"
    if "should" in lower:
        return "should"
    if " may " in lower or lower.startswith("may "):
        return "may"
    return None


def _infer_tags(content: str) -> list[str]:
    lower = content.lower()
    tags: list[str] = []
    seen: set[str] = set()
    for pattern, tag in _TAG_PATTERNS:
        if tag not in seen and pattern.search(lower):
            tags.append(tag)
            seen.add(tag)
    return tags


def parse_policy_markdown(path: str = _POLICY_PATH) -> List[PolicySection]:
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    sections: list[PolicySection] = []
    # Each entry: (line_index, heading_level, section_id, title)
    heading_positions: list[tuple[int, int, str, str]] = []

    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.rstrip())
        if m:
            hashes, sec_id, title = m.group(1), m.group(2), m.group(3).strip()
            level = len(hashes)
            heading_positions.append((i, level, sec_id, title))

    for idx, (line_idx, level, sec_id, title) in enumerate(heading_positions):
        # Collect content until next heading of same or higher level (fewer #'s)
        end_line = len(lines)
        for future_idx, future_level, _, _ in heading_positions[idx + 1 :]:
            if future_level <= level:
                end_line = future_idx
                break

        content = "".join(lines[line_idx:end_line]).rstrip()
        domain = _infer_domain(sec_id)
        modality = _infer_modality(content)
        tags = _infer_tags(content)

        sections.append(
            PolicySection(
                section_id=sec_id,
                title=title,
                heading_level=level,
                content=content,
                domain=domain,
                modality=modality,
                tags=tags,
            )
        )

    return sections
