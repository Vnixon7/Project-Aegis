from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional


class DecisionStatus(str, Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCK = "BLOCK"
    SUBSTRATE_FREEZE = "SUBSTRATE_FREEZE"
    DIAGNOSTIC_MODE = "DIAGNOSTIC_MODE"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    PARTIAL = "PARTIAL"
    CRASHED = "CRASHED"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    LOW_CONF = "LOW_CONF"


class IntegrityTier(IntEnum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4


@dataclass(frozen=True)
class Fact:
    key: str
    value: Any
    confidence: float
    timestamp: datetime
    provenance_tier: IntegrityTier


@dataclass(frozen=True)
class Risk:
    key: str
    severity: float
    provenance_tier: IntegrityTier
    description: str = ""


@dataclass(frozen=True)
class Missingness:
    key: str
    critical: bool
    first_seen: datetime
    reason: str = ""


@dataclass(frozen=True)
class SubstrateContract:
    facts: Dict[str, Fact] = field(default_factory=dict)
    risks: Dict[str, Risk] = field(default_factory=dict)
    missingness: Dict[str, Missingness] = field(default_factory=dict)
    uncertainties: Dict[str, float] = field(default_factory=dict)  # key -> entropy [0,1]
    quarantine: Dict[str, Fact] = field(default_factory=dict)


@dataclass(frozen=True)
class TargetAnchor:
    key: str
    anchor_type: str
    score: float
    reason: str


@dataclass(frozen=True)
class EpistemicArgument:
    claim: DecisionStatus
    anchors: List[str]
    evidence_weight: float
    uncertainty_impact: float
    logic_trace: str


@dataclass(frozen=True)
class ResolutionTrace:
    status: DecisionStatus
    p_net: float
    proponent_score: float
    dissenter_score: float
    dominant_anchors: List[str]
    reason: str


@dataclass(frozen=True)
class AegisAction:
    status: DecisionStatus
    p_net: float
    dominant_anchors: List[str]
    trace: str
    can_execute: bool


@dataclass(frozen=True)
class ExternalEvidenceArtifact:
    probe_id: str
    status: ExecutionStatus
    source_tier: IntegrityTier
    confidence: float
    content: Dict[str, Any] = field(default_factory=dict)
    target_keys: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provenance: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Tier4Assertion:
    assertion_id: str
    message: str
    related_anchors: List[str]
    signed_by: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
