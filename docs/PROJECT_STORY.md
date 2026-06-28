## Inspiration

I built CrisisProcure AI from a reality I know too well: in many African hospitals and emergency response settings, urgency is constant but procurement workflows are not. During outbreaks, floods, transport disruptions, or power instability, the problem is rarely just "we need supplies". The real problem is time lost between request, approval, sourcing, and compliance checks.

In high-pressure moments, teams are forced to improvise across WhatsApp messages, emails, spreadsheets, and phone calls. People do heroic work, but the system is fragile. A delayed approval or missing document can mean critical stockouts.

CrisisProcure AI was inspired by this gap: we need procurement that moves at emergency speed without abandoning governance. I wanted to prove that agents, automation, and humans can work together in a way that is practical for African enterprise and public-sector realities.

## What it does

CrisisProcure AI is an agentic emergency procurement commander orchestrated with UiPath Maestro BPMN on UiPath Automation Cloud.

It takes urgent supply requests and moves them through a compliant end-to-end flow:
- Ingests emergency requisitions from multiple channels.
- Normalizes unstructured requests into clean, actionable procurement data.
- Scores policy and budget risk using a compliance-risk agent.
- Routes high-risk requests to human procurement leads for approval.
- Coordinates sourcing, purchase order creation, and escalation paths.
- Prioritizes concurrent requests so the most critical needs are handled first.

The outcome: urgent requests are converted into auditable, human-approved purchase actions in minutes, not days.

## How we built it

I built this as a solo project with UiPath as the orchestration control plane.

Core build stack:
- UiPath Maestro BPMN for process orchestration and decision gateways.
- UiPath Automation Cloud for execution, governance, and visibility.
- RPA/API tasks for intake and downstream procurement actions.
- Two coded agent APIs (FastAPI):
  - Compliance-Risk Agent for policy/budget risk scoring.
  - Prioritization Agent for emergency request ranking and escalation recommendations.

Design approach:
- Model the process in BPMN first so every handoff is explicit.
- Keep humans in the loop at high-risk checkpoints.
- Add retries, timeout branches, and manual fallback queues.
- Build for explainability so judges and operators can see why a path was chosen.

## Challenges we ran into

1. Balancing speed with compliance
Emergency workflows demand fast action, but procurement controls cannot be bypassed. The hardest part was designing branches that accelerate low-risk requests while forcing human review for risky ones.

2. Modeling real-world uncertainty
Crisis data is messy. Requests come incomplete, suppliers change availability, and urgency shifts by the hour. Building robust normalization and prioritization logic without overengineering was a constant tradeoff.

3. Solo execution pressure
As a one-person team on a deadline, context switching between architecture, coding, testing, documentation, and demo prep was intense. I had to ruthlessly focus on the smallest end-to-end flow that proves real value.

4. Storytelling under time constraints
A technically correct solution is not enough in a hackathon. I had to make architecture and business impact legible in under 5 minutes, while still showing real execution evidence.

## Accomplishments that we're proud of

- Built a working, end-to-end agentic procurement flow on UiPath Automation Cloud.
- Demonstrated human-in-the-loop governance for high-risk emergency requests.
- Implemented coded agents that are practical, explainable, and orchestration-friendly.
- Produced a resilient design with retries, escalations, and audit trail visibility.
- Delivered a complete submission package as a solo builder: repo, architecture, demo script, and project narrative.

## What we learned

- Agentic systems are strongest when orchestration is explicit and humans remain accountable at decision boundaries.
- BPMN is powerful for turning AI-assisted ideas into operationally reliable enterprise workflows.
- In emergency contexts, prioritization logic can be as important as prediction quality.
- Shipping a clear, tested MVP beats building a broad but shallow prototype.
- Constraints can sharpen creativity: building from African operational realities led to a solution focused on resilience, transparency, and practicality.

## What's next for CrisisProcure AI

- Integrate supplier reliability signals (lead time variance, fulfillment history) into risk and prioritization decisions.
- Add multilingual intake support for broader regional usability.
- Introduce adaptive policy packs for different sectors (healthcare, disaster response, utilities, public procurement).
- Add KPI dashboards for response-time reduction, approval latency, and stockout prevention.
- Pilot with real procurement teams and iterate toward production hardening, security certification, and broader deployment.
