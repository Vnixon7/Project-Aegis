from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from aegis.schema import (
    DecisionStatus,
    ExecutionStatus,
    ExternalEvidenceArtifact,
    Fact,
    IntegrityTier,
    Missingness,
    Risk,
    SubstrateContract,
)


class DefaultGateway:
    """
    Deterministic sensory layer.

    Non-success artifacts never resolve uncertainty or missingness.
    They instead increase uncertainty, add risk, or open critical gaps.
    """

    OBSERVABILITY_KEY = "R_OBSERVABILITY"
    TOOLING_KEY = "R_TOOLING_FAILURE"
    STALENESS_KEY = "R_STALENESS"

    def process(self, artifact: Any, sc: SubstrateContract | None) -> SubstrateContract:
        sc = sc or SubstrateContract()
        artifact = self._coerce_artifact(artifact)

        facts = dict(sc.facts)
        risks = dict(sc.risks)
        missing = dict(sc.missingness)
        uncertainties = dict(sc.uncertainties)
        quarantine = dict(sc.quarantine)

        status = artifact.status
        now = artifact.timestamp
        target_keys = artifact.target_keys or [artifact.probe_id]

        if status == ExecutionStatus.SUCCESS:
            existing = facts.get(artifact.probe_id)
            if not existing or artifact.source_tier <= existing.provenance_tier:
                facts[artifact.probe_id] = Fact(
                    key=artifact.probe_id,
                    value=artifact.content,
                    confidence=max(0.0, min(1.0, artifact.confidence)),
                    timestamp=now,
                    provenance_tier=artifact.source_tier,
                )
                missing.pop(artifact.probe_id, None)
                uncertainties[artifact.probe_id] = max(0.0, uncertainties.get(artifact.probe_id, 0.05) * 0.8)
            # Lower-tier success never overwrites; ignore silently by design.

        elif status == ExecutionStatus.TIMEOUT:
            missing[artifact.probe_id] = Missingness(
                key=artifact.probe_id,
                critical=True,
                first_seen=missing.get(artifact.probe_id, Missingness(artifact.probe_id, True, now)).first_seen,
                reason="PROBE_TIMEOUT",
            )
            for key in target_keys:
                uncertainties[key] = self._widen(uncertainties.get(key, 0.3), 0.2)
            risks[self.OBSERVABILITY_KEY] = self._bump_risk(self.OBSERVABILITY_KEY, risks.get(self.OBSERVABILITY_KEY), 0.10, IntegrityTier.TIER_2, "Observability degraded by timeout.")

        elif status == ExecutionStatus.PARTIAL:
            for key in target_keys:
                uncertainties[key] = self._widen(uncertainties.get(key, 0.25), 0.15)
            quarantine[f"QUARANTINE_{artifact.probe_id}"] = Fact(
                key=f"QUARANTINE_{artifact.probe_id}",
                value=artifact.content,
                confidence=max(0.0, min(0.4, artifact.confidence)),
                timestamp=now,
                provenance_tier=min(artifact.source_tier + 1, IntegrityTier.TIER_4),
            )

        elif status == ExecutionStatus.CRASHED:
            missing[artifact.probe_id] = Missingness(
                key=artifact.probe_id,
                critical=True,
                first_seen=missing.get(artifact.probe_id, Missingness(artifact.probe_id, True, now)).first_seen,
                reason="RUNNER_CRASH",
            )
            for key in target_keys:
                uncertainties[key] = self._widen(uncertainties.get(key, 0.35), 0.25)
            risks[self.TOOLING_KEY] = self._bump_risk(self.TOOLING_KEY, risks.get(self.TOOLING_KEY), 0.20, IntegrityTier.TIER_1, "Probe runner or parser crashed.")

        elif status == ExecutionStatus.CONFLICT:
            for key in target_keys:
                uncertainties[key] = max(uncertainties.get(key, 0.0), 0.95)
            risks[self.OBSERVABILITY_KEY] = self._bump_risk(self.OBSERVABILITY_KEY, risks.get(self.OBSERVABILITY_KEY), 0.15, IntegrityTier.TIER_1, "Conflicting artifacts detected.")

        elif status == ExecutionStatus.STALE:
            for key in target_keys:
                uncertainties[key] = self._widen(uncertainties.get(key, 0.2), 0.05)
            risks[self.STALENESS_KEY] = self._bump_risk(self.STALENESS_KEY, risks.get(self.STALENESS_KEY), 0.10, IntegrityTier.TIER_2, "Artifact is stale relative to current environment.")

        elif status == ExecutionStatus.LOW_CONF:
            for key in target_keys:
                uncertainties[key] = self._widen(uncertainties.get(key, 0.2), 0.05)
            quarantine[f"QUARANTINE_{artifact.probe_id}"] = Fact(
                key=f"QUARANTINE_{artifact.probe_id}",
                value=artifact.content,
                confidence=max(0.0, min(0.3, artifact.confidence)),
                timestamp=now,
                provenance_tier=min(artifact.source_tier + 1, IntegrityTier.TIER_4),
            )

        return SubstrateContract(
            facts=facts,
            risks=risks,
            missingness=missing,
            uncertainties=uncertainties,
            quarantine=quarantine,
        )

    def _coerce_artifact(self, artifact: Any) -> ExternalEvidenceArtifact:
        if isinstance(artifact, ExternalEvidenceArtifact):
            return artifact
        return ExternalEvidenceArtifact(
            probe_id=artifact.probe_id,
            status=artifact.status,
            source_tier=artifact.source_tier,
            confidence=getattr(artifact, "confidence", 0.0),
            content=getattr(artifact, "content", {}),
            target_keys=getattr(artifact, "target_keys", []) or [artifact.probe_id],
            timestamp=getattr(artifact, "timestamp", datetime.utcnow()),
            provenance=getattr(artifact, "provenance", {}),
        )

    @staticmethod
    def _widen(current: float, delta: float) -> float:
        return round(min(1.0, max(0.0, current + delta)), 4)

    @staticmethod
    def _bump_risk(key: str, existing: Risk | None, delta: float, tier: IntegrityTier, description: str) -> Risk:
        if existing is None:
            return Risk(key=key, severity=min(1.0, delta), provenance_tier=tier, description=description)
        return replace(existing, severity=round(min(1.0, existing.severity + delta), 4))
