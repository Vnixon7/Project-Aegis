from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import pvariance
from typing import List, Optional

from aegis.schema import (
    DecisionStatus,
    EpistemicArgument,
    IntegrityTier,
    ResolutionTrace,
    SubstrateContract,
)


class Arbiter:
    WEIGHTS = {
        IntegrityTier.TIER_1: 1.0,
        IntegrityTier.TIER_2: 0.75,
        IntegrityTier.TIER_3: 0.4,
        IntegrityTier.TIER_4: 0.2,
    }

    def resolve(
        self,
        sc: SubstrateContract,
        p_args: List[EpistemicArgument],
        d_args: List[EpistemicArgument],
        policy,
    ) -> ResolutionTrace:
        if any(m.critical for m in sc.missingness.values()):
            anchors = list(sc.missingness.keys())[:5]
            return ResolutionTrace(
                status=DecisionStatus.INSUFFICIENT_EVIDENCE,
                p_net=0.0,
                proponent_score=0.0,
                dissenter_score=0.0,
                dominant_anchors=anchors,
                reason="Critical missingness present; GO evaluation prohibited.",
            )

        p_score, p_anchors = self._score_arguments(sc, p_args, mode="proponent")
        d_score, d_anchors = self._score_arguments(sc, d_args, mode="dissenter")
        p_net = round(p_score - d_score, 4)

        if p_net >= getattr(policy, "go_threshold", 1.0):
            status = DecisionStatus.GO
            reason = "Proponent pressure exceeded GO threshold."
        elif p_net <= getattr(policy, "block_threshold", -0.5):
            status = DecisionStatus.BLOCK
            reason = "Dissenter pressure exceeded BLOCK threshold."
        else:
            status = DecisionStatus.CONDITIONAL_GO
            reason = "Mixed evidence; action remains conditionally constrained."

        return ResolutionTrace(
            status=status,
            p_net=p_net,
            proponent_score=round(p_score, 4),
            dissenter_score=round(d_score, 4),
            dominant_anchors=self._dominant_anchors(p_anchors, d_anchors),
            reason=reason,
        )

    def _score_arguments(self, sc: SubstrateContract, args: List[EpistemicArgument], mode: str):
        total = 0.0
        contribs = {}
        for arg in args:
            arg_total = 0.0
            for anchor in arg.anchors:
                tier_weight = self._anchor_tier_weight(sc, anchor)
                entropy_discount = self._anchor_entropy_discount(sc, anchor)
                polarity = self._anchor_polarity_weight(sc, anchor, mode)
                contribution = arg.evidence_weight * tier_weight * entropy_discount * polarity
                arg_total += contribution
                contribs[anchor] = contribs.get(anchor, 0.0) + contribution
            arg_total *= max(0.0, 1.0 - arg.uncertainty_impact)
            total += arg_total
        return total, contribs

    def _anchor_tier_weight(self, sc: SubstrateContract, anchor: str) -> float:
        if anchor in sc.facts:
            return self.WEIGHTS[sc.facts[anchor].provenance_tier]
        if anchor in sc.risks:
            return self.WEIGHTS[sc.risks[anchor].provenance_tier]
        if anchor in sc.missingness:
            return 1.0
        return 0.5

    def _anchor_entropy_discount(self, sc: SubstrateContract, anchor: str) -> float:
        entropy = sc.uncertainties.get(anchor, 0.0)
        if entropy > 0.8:
            return 0.4
        if entropy > 0.6:
            return 0.7
        return 1.0

    def _anchor_polarity_weight(self, sc: SubstrateContract, anchor: str, mode: str) -> float:
        if anchor in sc.risks:
            sev = sc.risks[anchor].severity
            return 1.0 + (0.5 * sev) if mode == "dissenter" else 0.8
        if anchor in sc.facts:
            conf = sc.facts[anchor].confidence
            return 1.0 + (0.25 * conf) if mode == "proponent" else 0.9
        if anchor in sc.missingness:
            return 1.5 if mode == "dissenter" else 0.1
        return 1.0

    @staticmethod
    def _dominant_anchors(p_anchors, d_anchors, top_k: int = 5):
        merged = dict(p_anchors)
        for k, v in d_anchors.items():
            merged[k] = merged.get(k, 0.0) + v
        return [k for k, _ in sorted(merged.items(), key=lambda kv: kv[1], reverse=True)[:top_k]]


@dataclass(frozen=True)
class DecisionSnapshot:
    timestamp: datetime
    status: DecisionStatus
    p_net: float
    dominant_anchors: List[str]


class ConvergenceMonitor:
    def __init__(self, window_size: int = 6, threshold: int = 3, variance_threshold: float = 2.0):
        self.window: List[DecisionSnapshot] = []
        self.window_size = window_size
        self.threshold = threshold
        self.variance_threshold = variance_threshold

    def evaluate(self, trace: ResolutionTrace) -> Optional[DecisionStatus]:
        snap = DecisionSnapshot(datetime.utcnow(), trace.status, trace.p_net, trace.dominant_anchors)
        self.window.append(snap)
        self.window = self.window[-self.window_size :]

        if self._count_binary_flips() >= self.threshold:
            return DecisionStatus.SUBSTRATE_FREEZE
        if len(self.window) >= 3 and self._calculate_pnet_variance() > self.variance_threshold:
            return DecisionStatus.SUBSTRATE_FREEZE
        return None

    def _count_binary_flips(self) -> int:
        if len(self.window) < 2:
            return 0
        flips = 0
        for i in range(1, len(self.window)):
            prev = self.window[i - 1].status
            curr = self.window[i].status
            if (prev == DecisionStatus.GO and curr in {DecisionStatus.BLOCK, DecisionStatus.INSUFFICIENT_EVIDENCE}) or (
                curr == DecisionStatus.GO and prev in {DecisionStatus.BLOCK, DecisionStatus.INSUFFICIENT_EVIDENCE}
            ):
                flips += 1
        return flips

    def _calculate_pnet_variance(self) -> float:
        if len(self.window) < 2:
            return 0.0
        return pvariance([item.p_net for item in self.window])
