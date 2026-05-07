from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class PolicySection:
    section_id: str
    title: str
    heading_level: int
    content: str
    domain: str
    modality: Optional[str]
    tags: List[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PolicySection":
        return cls(**d)


@dataclass
class PolicyRule:
    rule_id: str
    section_id: str
    text: str
    modality: str  # "may" | "must" | "must_not" | "should"
    domain: str
    action: Optional[str] = None
    data_types: List[str] = field(default_factory=list)
    resource_types: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    trust_tiers: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    precedence: int = 50
    risk_level: str = "low"
    references: List[str] = field(default_factory=list)
    exception_to: List[str] = field(default_factory=list)
    overrides: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PolicyRule":
        return cls(**d)


@dataclass
class PolicyConflict:
    conflict_id: str
    conflict_type: str  # "explicit_exception" | "explicit_override" | "implicit_modality_conflict"
    rule_ids: List[str]
    section_ids: List[str]
    risk_level: str
    resolution_hint: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PolicyConflict":
        return cls(**d)


@dataclass
class PolicyEvidenceBundle:
    sections: List[PolicySection]
    rules: List[PolicyRule]
    graph_expanded_rules: List[PolicyRule]
    conflicts: List[PolicyConflict]

    def to_dict(self) -> dict:
        return {
            "sections": [s.to_dict() for s in self.sections],
            "rules": [r.to_dict() for r in self.rules],
            "graph_expanded_rules": [r.to_dict() for r in self.graph_expanded_rules],
            "conflicts": [c.to_dict() for c in self.conflicts],
        }
