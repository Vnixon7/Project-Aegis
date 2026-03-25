from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional
from datetime import datetime

class DecisionStatus(str, Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCK = "BLOCK"
    SUBSTRATE_FREEZE = "SUBSTRATE_FREEZE"

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    CRASHED = "CRASHED"

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

@dataclass(frozen=True)
class Missingness:
    key: str
    critical: bool
    first_seen: datetime

@dataclass(frozen=True)
class SubstrateContract:
    facts: Dict[str, Fact] = field(default_factory=dict)
    risks: Dict[str, Risk] = field(default_factory=dict)
    missingness: Dict[str, Missingness] = field(default_factory=dict)
    uncertainties: Dict[str, float] = field(default_factory=dict) # Key -> Entropy
