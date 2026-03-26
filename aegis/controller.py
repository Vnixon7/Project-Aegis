from __future__ import annotations

from typing import Any, Iterable, Optional

from aegis.schema import AegisAction, DecisionStatus, SubstrateContract, Tier4Assertion


class AegisController:
    """Orchestration-only controller for Project Aegis."""

    def __init__(self, gateway, targeting, arbiter, monitor, policy):
        self.gateway = gateway
        self.targeting = targeting
        self.arbiter = arbiter
        self.monitor = monitor
        self.policy = policy
        self.sc: Optional[SubstrateContract] = None

    def tick(self, artifacts: Iterable[Any]) -> AegisAction:
        # 1. Ingest artifacts into the substrate.
        for artifact in artifacts:
            self.sc = self.gateway.process(artifact, self.sc)

        assert self.sc is not None, "Substrate must exist after gateway processing."

        # 2. Build deterministic arguments from the current substrate.
        p_args = self.targeting.build_proponent_arguments(self.sc)
        d_args = self.targeting.build_dissenter_arguments(self.sc)

        # 3. Resolve arguments mathematically.
        resolution = self.arbiter.resolve(self.sc, p_args, d_args, self.policy)

        # 4. Apply temporal guardrails.
        stability_override = self.monitor.evaluate(resolution)
        final_status = stability_override or resolution.status

        # 5. Emit hard execution gate.
        return AegisAction(
            status=final_status,
            p_net=resolution.p_net,
            dominant_anchors=resolution.dominant_anchors,
            trace=resolution.reason,
            can_execute=final_status == DecisionStatus.GO,
        )

    def force_thaw(self, human_assertion: Tier4Assertion) -> None:
        """Placeholder for a formal Tier-4 freeze recovery path."""
        raise NotImplementedError("Tier-4 thaw protocol is not yet implemented.")
