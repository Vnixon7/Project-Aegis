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
git clone [https://github.com/youruser/project_aegis.git](https://github.com/youruser/Project_Aegis.git)
cd project_aegis
```

## Quick Start
Run python main.py to see the system handle a high-entropy "Network Flap" scenario.


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

```


## Aegis Troubleshooting & Epistemic Calibration

This guide explains how to interpret the mathematical outputs of the Aegis Arbiter and how to resolve common system deadlocks.



## 1. The Decision Matrix: Interpreting $P_{net}$The $P_{net}$ score (Net Epistemic Pressure) represents the "Margin of Safety." While can_execute is a binary gate, the underlying score dictates the quality of the environment.
```mermaid
Pnet​           Range	       Status	            Meaning	                                                    Operational Action
> 2.0	       GO	           Strong Consensus.    High-tier facts are present with near-zero entropy.	        Standard automated execution.
1.0 to 2.0	   GO	           Nominal Safety.      Basic requirements met; standard noise levels.	            Standard automated execution.
0.0 to 1.0	   CONDITIONAL_GO  Fragile State.       Proponent outweighs Dissenter, but the margin is thin.      Warning: Reduce position size / increase monitoring.
-0.5 to 0.0	   INSUFFICIENT	   Opaque Reality.      Evidence is missing or too stale to calculate a safe path.  Hold: System waits for fresh artifacts.
< -0.5	       BLOCK	       Active Hostility.    Risks or tool failures outweigh successes.	                Stop: Hard execution block. Investigate logs.
```
## 2. Common System States & Fixes


State: Stuck in INSUFFICIENT_EVIDENCE
Symptom: The system refuses to move to GO despite "good" data.

The Cause: A Critical flag is active in the sc.missingness registry. Aegis follows a Short-Circuit Invariant: if a required probe is missing, no amount of other "Success" data can override it.

Resolution: 
1.  Check AegisAction.dominant_anchors to see which probe is missing.
2.  Verify the sensor/tool is actually reporting to the Gateway.
3.  If the probe is no longer relevant, update your TargetingEngine to remove the requirement.

State: SUBSTRATE_FREEZE (The Thrash Trigger)
Symptom: The status flips to SUBSTRATE_FREEZE and stops all processing.

The Cause: The ConvergenceMonitor detected too many status flips (e.g., GO -> BLOCK -> GO) within the defined window. This indicates Sensory Turbulence.

Resolution: 
1.  Do not immediately restart. Identify the "Flapping" sensor.
2.  Wait for the environment to stabilize (The "Cooling Period").
3.  Use a Tier-4 Assertion (Human Override) to acknowledge the volatility and force a transition to DIAGNOSTIC_MODE.

State: BLOCK despite Human (Tier-4) Success
Symptom: You manually told the system it is "OK," but it still returns BLOCK.

The Cause: Tier Weighting. A Tier-4 Assertion has a weight of 0.2. A Tier-1 Tool Crash or Risk has a weight of 1.0.

Resolution: Aegis is designed to trust automated, signed telemetry over human "guesses." To override a Tier-1 Risk, you must provide multiple corroborating assertions or fix the underlying Tier-1 evidence source.



## 3. Tuning Your Policy

If Aegis is being "too sensitive" or "too reckless," adjust your Policy thresholds:

Increase go_threshold: If you want the system to be more skeptical (requires more evidence to act).

Decrease block_threshold: If you want to allow the system to tolerate more minor risks before stopping.

Adjust ConvergenceMonitor(threshold=N): Increase N if your environment is naturally noisy but you want to avoid frequent Freezes.
