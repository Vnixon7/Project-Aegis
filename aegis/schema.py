from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

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
    TIER_1 = 1  # Signed automated artifacts
    TIER_2 = 2  # System logs/metrics
    TIER_3 = 3  # Model/Parser summaries
    TIER_4 = 4  # Human assertions

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
    description: str

@dataclass(frozen=True)
class Uncertainty:
    key: str
    entropy_score: float

@dataclass(frozen=True)
class Missingness:
    key: str
    critical: bool
    reason: str
    first_seen: datetime

@dataclass(frozen=True)
class SubstrateContract:
    facts: Dict[str, Fact] = field(default_factory=dict)
    risks: Dict[str, Risk] = field(default_factory=dict)
    uncertainties: Dict[str, Uncertainty] = field(default_factory=dict)
    missingness: Dict[str, Missingness] = field(default_factory=dict)
    status: DecisionStatus = DecisionStatus.INSUFFICIENT_EVIDENCE
