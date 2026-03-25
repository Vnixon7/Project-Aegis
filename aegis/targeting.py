from aegis.schema import *

@dataclass
class Argument:
    tier: IntegrityTier
    entropy: float
    weight: float

class DefaultTargeting:
    def rank_for_proponent(self, sc: SubstrateContract) -> List[Argument]:
        return [Argument(f.provenance_tier, 0.1, f.confidence) for f in sc.facts.values()]

    def rank_for_dissenter(self, sc: SubstrateContract) -> List[Argument]:
        args = [Argument(IntegrityTier.TIER_2, 0.5, 1.0) for _ in sc.missingness.values()]
        args += [Argument(r.provenance_tier, 0.2, r.severity) for r in sc.risks.values()]
        return args
