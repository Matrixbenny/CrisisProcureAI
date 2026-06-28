# BPMN MVP Design (for UiPath Maestro)

## Process name
EmergencyProcure-CrisisProcureAI

## Participants
- Requestor (human)
- Procurement Lead (human)
- RPA Bot (robot)
- Compliance-Risk Agent (coded agent API)
- Prioritization Agent (coded agent API)

## BPMN path
1. Start Event: Emergency requisition received
2. Service Task: Ingest requisition data (RPA/API)
3. Service Task: Normalize payload (AI agent)
4. Service Task: Compliance-risk scoring (Exception Agent API)
5. Exclusive Gateway: Risk decision
6. User Task: Procurement lead review (if high risk)
7. Service Task: Supplier shortlist and quote retrieval
8. Service Task: Budget and policy validation
9. Service Task: Purchase order creation
10. Service Task: Requisition prioritization (Collections Agent API)
11. User Task: Manual escalation for blocked requests (if needed)
12. End Event: Process completed with audit trail

## Required variables
- requisitionId
- requesterDepartment
- budgetClass
- riskScore
- exceptionDecision
- supplierId
- etaHours
- priorityLevel

## Failure and retry strategy
- API task retry: 3 attempts with exponential backoff
- Timeout route to human queue
- Non-recoverable errors create incident case and notify owner

## Human-in-the-loop controls
- Procurement lead approval mandatory for high-risk requisitions
- Policy override handling always assigned to human owner
- Manual override logging required for all forced approvals
