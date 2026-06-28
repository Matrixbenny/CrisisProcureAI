# 5-Minute Demo Script

## 0:00-0:30 Problem and value
"Emergency procurement breaks when urgent requests are incomplete, approvals stall, and policy checks happen too late. We built CrisisProcure AI on UiPath Maestro BPMN to orchestrate agents, robots, and people end-to-end."

## 0:30-1:20 Architecture
Show diagram and explain:
- UiPath Maestro BPMN is orchestration layer
- Exception Agent and Collections Agent as API services
- Human approvals for high-risk decision points

## 1:20-2:40 Live run: happy path
- Trigger a standard urgent requisition
- Show normalized procurement payload
- Show auto-approved low-risk decision
- Show downstream supplier shortlist and PO creation

## 2:40-4:10 Live run: exception path
- Trigger a high-risk requisition (policy or budget anomaly)
- Show high risk score and branch to procurement lead review
- Approve in human task and continue flow
- Show audit trail and run history

## 4:10-4:50 Prioritization intelligence
- Trigger multiple concurrent emergency requisitions
- Show prioritization recommendations
- Show blocked request routed to manual escalation

## 4:50-5:00 Closing
"This is a working enterprise orchestration with resilient routing, human governance, and clear business impact, built and run on UiPath Automation Cloud."

## Recording tips
- Keep terminal and UI zoomed for readability
- Avoid long waits; pre-stage data
- Keep one backup run prepared
