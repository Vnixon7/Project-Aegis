from __future__ import annotations

from dataclasses import dataclass
from typing import List

from aegis.schema import (
    DecisionStatus,
    EpistemicArgument,
    IntegrityTier,
    SubstrateContract,
    TargetAnchor,
)


class DefaultTargeting:
    TIER_WEIGHTS = {
        IntegrityTier.TIER_1: 1.0,
        IntegrityTier.TIER_2: 0.75,
        IntegrityTier.TIER_3: 0.4,
        IntegrityTier.TIER_4: 0.2,
    }

    def rank_for_proponent(self, sc: SubstrateContract, top_k: int = 5) -> List[TargetAnchor]:
        candidates: List[TargetAnchor] = []
        for key, fact in sc.facts.items():
            entropy = sc.uncertainties.get(key, 0.0)
            score = (fact.confidence * self.TIER_WEIGHTS[fact.provenance_tier]) * (1.0 - entropy)
            candidates.append(TargetAnchor(key=key, anchor_type="Fact", score=round(score, 4), reason="High-integrity evidence pillar"))
        return sorted(candidates, key=lambda x: x.score, reverse=True)[:top_k]

    def rank_for_dissenter(self, sc: SubstrateContract, top_k: int = 5) -> List[TargetAnchor]:
        candidates: List[TargetAnchor] = []

        for key, risk in sc.risks.items():
            entropy = sc.uncertainties.get(key, 0.0)
            score = (risk.severity * self.TIER_WEIGHTS[risk.provenance_tier]) * (1.0 + entropy)
            candidates.append(TargetAnchor(key=key, anchor_type="Risk", score=round(score, 4), reason="Structural risk detected"))

        for key, miss in sc.missingness.items():
            bonus = 2.0 if miss.critical else 1.0
            candidates.append(TargetAnchor(key=key, anchor_type="Missingness", score=bonus, reason="Critical visibility gap"))

        for key, entropy in sc.uncertainties.items():
            if entropy > 0.7:
                candidates.append(TargetAnchor(key=key, anchor_type="Uncertainty", score=round(entropy, 4), reason="High entropy volatility"))

        return sorted(candidates, key=lambda x: x.score, reverse=True)[:top_k]

    def build_proponent_arguments(self, sc: SubstrateContract, top_k: int = 5) -> List[EpistemicArgument]:
        anchors = self.rank_for_proponent(sc, top_k=top_k)
        return [
            EpistemicArgument(
                claim=DecisionStatus.GO,
                anchors=[a.key],
                evidence_weight=a.score,
                uncertainty_impact=sc.uncertainties.get(a.key, 0.0),
                logic_trace=a.reason,
            )
            for a in anchors
        ]

    def build_dissenter_arguments(self, sc: SubstrateContract, top_k: int = 5) -> List[EpistemicArgument]:
        anchors = self.rank_for_dissenter(sc, top_k=top_k)
        claim = DecisionStatus.BLOCK if any(a.anchor_type == "Risk" for a in anchors) else DecisionStatus.INSUFFICIENT_EVIDENCE
        return [
            EpistemicArgument(
                claim=claim,
                anchors=[a.key],
                evidence_weight=a.score,
                uncertainty_impact=sc.uncertainties.get(a.key, 0.0),
                logic_trace=a.reason,
            )
            for a in anchors
        ]
