from aegis.schema import *

class Arbiter:
    TIER_WEIGHTS = {
        IntegrityTier.TIER_1: 1.0,
        IntegrityTier.TIER_2: 0.75,
        IntegrityTier.TIER_3: 0.4,
        IntegrityTier.TIER_4: 0.2
    }

    def resolve(self, sc: SubstrateContract, p_args: List[Any], d_args: List[Any], policy: Any):
        # 1. Short-circuit on Critical Missingness
        if any(m.critical for m in sc.missingness.values()):
            return DecisionStatus.INSUFFICIENT_EVIDENCE, 0.0

        # 2. Simplified P_net logic for Sprint 2/3
        p_score = sum(self.TIER_WEIGHTS[a.tier] * (1 - a.entropy) for a in p_args)
        d_score = sum(self.TIER_WEIGHTS[a.tier] * (1 + a.entropy) for a in d_args)
        p_net = p_score - d_score

        if p_net >= policy.go_threshold: return DecisionStatus.GO, p_net
        if p_net <= policy.block_threshold: return DecisionStatus.BLOCK, p_net
        return DecisionStatus.CONDITIONAL_GO, p_net

class ConvergenceMonitor:
    def __init__(self, window_size=6, flip_threshold=3):
        self.history = []
        self.window_size = window_size
        self.flip_threshold = flip_threshold

    def evaluate(self, status: DecisionStatus) -> Optional[DecisionStatus]:
        self.history.append(status)
        self.history = self.history[-self.window_size:]
        
        if len(self.history) < self.window_size:
            return None

        flips = 0
        for i in range(1, len(self.history)):
            if self.history[i] != self.history[i-1]:
                flips += 1
        
        return DecisionStatus.SUBSTRATE_FREEZE if flips >= self.flip_threshold else None
