from aegis.schema import *
from aegis.engine import Arbiter, ConvergenceMonitor

class AegisController:
    def __init__(self, gateway, targeting, arbiter, monitor, policy):
        self.gateway = gateway
        self.targeting = targeting
        self.arbiter = arbiter
        self.monitor = monitor
        self.policy = policy
        self.current_sc = SubstrateContract()

    def tick(self, artifacts: List[Any]):
        # 1. Ingest
        for art in artifacts:
            self.current_sc = self.gateway.process(art, self.current_sc)

        # 2. Target & Resolve
        p_anchors = self.targeting.rank_for_proponent(self.current_sc)
        d_anchors = self.targeting.rank_for_dissenter(self.current_sc)
        
        status, p_net = self.arbiter.resolve(self.current_sc, p_anchors, d_anchors, self.policy)

        # 3. Monitor
        override = self.monitor.evaluate(status)
        final_status = override or status

        return {
            "status": final_status,
            "can_execute": final_status == DecisionStatus.GO,
            "p_net": p_net
        }
