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
