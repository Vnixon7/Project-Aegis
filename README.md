# Project Aegis: Epistemic Decision Gating

**Aegis** is a deterministic safety layer for autonomous systems (Trading, ML Deployment, Robotics). Unlike traditional "if-then" logic, Aegis models **uncertainty, missingness, and signal integrity** to prevent actions when the environment is unstable.

## Core Architecture
1. **Substrate:** A unified contract representing the system's "belief" about reality.
2. **Integrity Tiers:** Evidence is weighted by its source (Tier 1: Signed Artifacts → Tier 4: Human Assertions).
3. **MAER (Multi-Agent Epistemic Reasoning):** A Proponent and Dissenter argue over the substrate; an Arbiter calculates the mathematical net pressure ($P_{net}$).
4. **Convergence Monitor:** Detects "thrashing" (oscillating decisions) and triggers a `SUBSTRATE_FREEZE`.

## Installation
```bash
# Clone the repository
git clone [https://github.com/youruser/project_aegis.git](https://github.com/youruser/project_aegis.git)
cd project_aegis

## Quick Start
Run python main.py to see the system handle a high-entropy "Network Flap" scenario.


---

### 2. main.py
This is your functional entry point. It simulates a "Fragile Success" scenario where a successful load test is undermined by rising network risks.

```python
from datetime import datetime
from dataclasses import dataclass
from aegis.schema import DecisionStatus, ExecutionStatus, IntegrityTier
from aegis.gatekeeper import DefaultGateway
from aegis.targeting import DefaultTargeting
from aegis.engine import Arbiter, ConvergenceMonitor
from aegis.controller import AegisController

# 1. Define Environment Policy
@dataclass
class TradingPolicy:
    go_threshold: float = 1.0     # Required P_net to allow trade
    block_threshold: float = -0.5 # P_net that triggers a hard stop

# 2. Mock Evidence Artifact (What your sensors send to Aegis)
@dataclass
class EvidenceArtifact:
    probe_id: str
    status: ExecutionStatus
    source_tier: IntegrityTier
    confidence: float
    content: dict

def run_simulation():
    # Initialize the Epistemic Stack
    aegis = AegisController(
        gateway=DefaultGateway(),
        targeting=DefaultTargeting(),
        arbiter=Arbiter(),
        monitor=ConvergenceMonitor(window_size=4, threshold=2),
        policy=TradingPolicy()
    )

    print(f"{'Tick':<5} | {'Artifact Status':<15} | {'Aegis Decision':<20} | {'Execute?'}")
    print("-" * 65)

    # SCENARIO: A stable system that begins to "Thrash" due to a flaky network probe
    scenarios = [
        EvidenceArtifact("NET_PROBE", ExecutionStatus.SUCCESS, IntegrityTier.TIER_1, 0.95, {"latency": "5ms"}),
        EvidenceArtifact("NET_PROBE", ExecutionStatus.TIMEOUT, IntegrityTier.TIER_1, 0.0, {}),
        EvidenceArtifact("NET_PROBE", ExecutionStatus.SUCCESS, IntegrityTier.TIER_1, 0.95, {"latency": "6ms"}),
        EvidenceArtifact("NET_PROBE", ExecutionStatus.TIMEOUT, IntegrityTier.TIER_1, 0.0, {}),
    ]

    for i, artifact in enumerate(scenarios):
        # The 'tick' is the atomic unit of Aegis reasoning
        result = aegis.tick([artifact])
        
        tick_num = i + 1
        status_str = artifact.status.value
        decision = result["status"].value
        can_exec = "YES" if result["can_execute"] else "NO"
        
        print(f"{tick_num:<5} | {status_str:<15} | {decision:<20} | {can_exec}")

    print("-" * 65)
    print("Simulation Complete: Aegis detected instability and enforced a SUBSTRATE_FREEZE.")

if __name__ == "__main__":
    run_simulation()
