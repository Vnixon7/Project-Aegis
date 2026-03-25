from aegis.schema import SubstrateContract, DecisionStatus

class AegisController:
    def __init__(self, gateway, targeting, arbiter, monitor, policy):
        self.gateway, self.targeting = gateway, targeting
        self.arbiter, self.monitor = arbiter, monitor
        self.policy = policy
        self.sc = SubstrateContract()

    def tick(self, artifacts):
        for art in artifacts:
            self.sc = self.gateway.process(art, self.sc)
            
        p_args = self.targeting.rank_for_proponent(self.sc)
        d_args = self.targeting.rank_for_dissenter(self.sc)
        
        status, p_net = self.arbiter.resolve(self.sc, p_args, d_args, self.policy)
        override = self.monitor.evaluate(status)
        final_status = override or status
        
        return {"status": final_status, "can_execute": final_status == DecisionStatus.GO, "p_net": p_net}
