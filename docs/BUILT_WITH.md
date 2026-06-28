# Built With

## Devpost short format (paste into "Built with")
UiPath Maestro BPMN, UiPath Automation Cloud, UiPath Robots, UiPath API Workflows, Python, FastAPI, Uvicorn, Pydantic, REST APIs, JSON, GitHub, Markdown, Mermaid

## Devpost keyword-optimized one-liner
UiPath Maestro BPMN, UiPath Automation Cloud, Agentic AI, Enterprise Automation, Human-in-the-Loop, RPA, API Workflows, Python, FastAPI, REST API, JSON, GitHub

## Detailed stack
- Orchestration platform: UiPath Maestro BPMN, UiPath Automation Cloud
- Automation layer: UiPath Robots, UiPath API Workflows
- Agent services: Python 3.10+, FastAPI, Uvicorn, Pydantic
- Integration: REST APIs, JSON payload contracts
- Development workflow: GitHub, coding-agent-assisted development
- Documentation and architecture: Markdown, Mermaid diagrams

## Future-ready architecture choices
- Contract-first API design: Agent services communicate through stable JSON schemas to allow service upgrades without breaking BPMN flow.
- Swap-friendly agent layer: The current coded agents can be replaced or enhanced with new models/providers while keeping UiPath as control plane.
- Human-in-the-loop by design: High-risk branches remain explicit, so stricter policy rules can be added later without redesigning the whole process.
- Resilience and change safety: Retry, timeout, and escalation patterns in BPMN support new integrations and partial failures.
- Scale path: The same orchestration can expand from a single emergency procurement flow to multi-site, multi-department process variants.

## Planned next integrations
- ERP connectors for automated PO posting and status sync
- Supplier reliability scoring service
- KPI dashboarding for request-to-PO and approval latency
- Multilingual request intake for broader regional adoption
