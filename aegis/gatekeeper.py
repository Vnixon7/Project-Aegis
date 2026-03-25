from aegis.schema import *

class DefaultGateway:
    def process(self, artifact: Any, sc: SubstrateContract) -> SubstrateContract:
        # Create copies to maintain immutability
        facts, risks, missing = dict(sc.facts), dict(sc.risks), dict(sc.missingness)
        
        if artifact.status != ExecutionStatus.SUCCESS:
            missing[artifact.probe_id] = Missingness(artifact.probe_id, True, datetime.utcnow())
        else:
            # Tier Protection: Only overwrite if tier is equal or better (lower number)
            existing = facts.get(artifact.probe_id)
            if not existing or artifact.source_tier <= existing.provenance_tier:
                facts[artifact.probe_id] = Fact(
                    artifact.probe_id, artifact.content, 
                    artifact.confidence, datetime.utcnow(), artifact.source_tier
                )
                missing.pop(artifact.probe_id, None)
                
        return SubstrateContract(facts=facts, risks=risks, missingness=missing)
