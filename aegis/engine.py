from typing import List, Tuple, Optional
from aegis.schema import DecisionStatus, IntegrityTier

class Arbiter:
    WEIGHTS = {IntegrityTier.TIER_1: 1.0, IntegrityTier.TIER_2: 0.75, IntegrityTier.TIER_3: 0.4, IntegrityTier.TIER_4: 0.2}

    def resolve(self, sc, p_args, d_args, policy) -> Tuple[DecisionStatus, float]:
        if any(m.critical for m in sc.missingness.values()):
            return DecisionStatus.INSUFFICIENT_EVIDENCE, 0.0
            
        p_score = sum(self.WEIGHTS[a.tier] * (1 - a.entropy) * a.weight for a in p_args)
        d_score = sum(self.WEIGHTS[a.tier] * (1 + a.entropy) * a.weight for a in d_args)
        p_net = p_score - d_score

        if p_net >= policy.go_threshold: return DecisionStatus.GO, p_net
        if p_net <= policy.block_threshold: return DecisionStatus.BLOCK, p_net
        return DecisionStatus.CONDITIONAL_GO, p_net

class ConvergenceMonitor:
    def __init__(self, window_size=5, threshold=3):
        self.history = []
        self.window_size, self.threshold = window_size, threshold

    def evaluate(self, status: DecisionStatus) -> Optional[DecisionStatus]:
        self.history.append(status)
        self.history = self.history[-self.window_size:]
        if len(self.history) < self.window_size: return None
        
        flips = sum(1 for i in range(1, len(self.history)) if self.history[i] != self.history[i-1])
        return DecisionStatus.SUBSTRATE_FREEZE if flips >= self.threshold else None
