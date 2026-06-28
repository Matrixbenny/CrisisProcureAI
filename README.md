# CrisisProcure AI: Agentic Emergency Procurement Commander on UiPath Maestro BPMN

Track: UiPath Maestro BPMN (Track 2)

## What this project does
CrisisProcure AI automates emergency procure-to-order flow with a human-in-the-loop model:
- RPA and API ingestion capture urgent requisitions from email/forms/ERP triggers.
- An AI normalization agent converts free-form requests into structured procurement intents.
- A compliance-risk agent scores policy, budget, and urgency risk with explainable rule traces.
- Maestro BPMN orchestrates sourcing, approval, PO creation, and supplier confirmation.
- A prioritization agent ranks pending requisitions using transparent policy-based scoring.

The result is faster time-to-PO, fewer manual handoffs, and stronger compliance under pressure.

## Why this matters
Emergency procurement is high-pressure, cross-system, and exception-heavy. Teams lose time reconciling incomplete requests, finding suppliers, and documenting approvals during incidents. This solution improves response speed while keeping humans in control of high-risk decisions.

## UiPath components used
- UiPath Maestro BPMN (primary orchestration)
- UiPath Automation Cloud (execution and governance)
- UiPath Robots / RPA workflows (requisition ingestion and ERP actions)
- UiPath API Workflows (external service integration)
- Human tasks and approvals in process handoff points

## Coding agents and external AI usage
This project demonstrates coding-agent-assisted development for:
- Agent API scaffolding
- Exception rule and confidence logic
- Prompt and integration documentation

External AI agents can be used behind API endpoints, while UiPath remains the orchestration and governance control plane.

## Repository structure
- docs/: Submission, architecture, demo, judging map, and execution plan
- bpmn/: BPMN process definition starter
- services/exception_agent/: Policy-driven compliance-risk service with explainability output
- services/collections_agent/: Policy-driven requisition prioritization service
- uipath/: Place exported UiPath assets or package references
- assets/: Screenshots, diagrams, and demo media references

## Quick start (local agent services)
1. Create and activate a Python environment.
2. Install dependencies:
   - pip install -r requirements.txt
3. Run exception agent:
   - uvicorn services.exception_agent.app:app --host 0.0.0.0 --port 8010
4. Run collections agent:
   - uvicorn services.collections_agent.app:app --host 0.0.0.0 --port 8020

## API features that improve trust and resilience
- Policy packs: both agents load configurable policy files from their service directories.
- Explainability: responses include triggered rules, policy versions, and recommended next step.
- Deterministic routing: risk and priority decisions map to explicit workflow lanes.
- Human governance: high-risk cases remain routed to mandatory human approvals.

## Quality checks
- Run syntax check:
   - python -m compileall services
- Run tests:
   - pytest -q

## Long-term roadmap
- See docs/WORLDCLASS_ROADMAP.md for present-to-future evolution plan.

Note: UiPath orchestration execution must run in UiPath Automation Cloud for hackathon compliance.

## Setup prerequisites
- UiPath Automation Cloud tenant with Maestro BPMN access
- UiPath Studio / Maestro design permissions
- Python 3.10+
- Access to sample requisition and supplier test data

## Team
Solo builder: this repository and demo are developed and maintained by a one-person team.

## End-to-end flow (MVP)
1. Intake urgent requisition from email or API
2. Normalize requisition payload with AI agent
3. Evaluate policy and budget risk score
4. Route high-risk items to procurement lead human task
5. Continue sourcing and supplier selection
6. Trigger PO creation and confirmation
7. Run prioritization for pending emergency requisitions
8. Close process with audit trail

## Demo checklist
- Show BPMN diagram in Maestro
- Trigger one happy path requisition
- Trigger one exception path with human approval
- Show prioritization recommendation output
- Show logs and handoff visibility in UiPath

## Try it out
- Source code: https://github.com/Matrixbenny/CrisisProcureAI
- Project story: docs/PROJECT_STORY.md
- Architecture: docs/ARCHITECTURE.md
- Built with: docs/BUILT_WITH.md
- Devpost-ready links list: docs/TRY_IT_OUT_LINKS.md

## License
MIT (see LICENSE)
