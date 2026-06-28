# Devpost Submission Draft

## Project title
CrisisProcure AI

## Track
UiPath Maestro BPMN (Track 2)

## Elevator pitch
CrisisProcure AI is an agentic emergency procurement commander that uses UiPath Maestro to turn urgent supply requests into compliant, human-approved purchase orders in minutes.

## Team
Solo builder (team size: 1)

## Problem
Emergency procurement during incidents is fragmented across email, forms, ERP, and chat channels. Teams spend too much time clarifying incomplete requests, checking policy constraints, finding available suppliers, and collecting approvals. This causes response delays, compliance risk, and low visibility.

## Solution
We built an end-to-end BPMN workflow on UiPath Automation Cloud that orchestrates humans, robots, APIs, and coded agents.
- Ingestion captures urgent requisitions from multiple channels
- AI normalization standardizes request payloads
- Compliance-risk Agent computes risk and routes high-risk items to procurement lead approval
- Maestro BPMN coordinates sourcing, approval, PO creation, and confirmation
- Prioritization Agent ranks pending requisitions and proposes escalation paths

## Architecture highlights
- UiPath Maestro BPMN is the orchestration control plane
- Coded agents exposed as API services
- Human tasks at key governance points
- Retry and fallback paths for resilience

## What makes this innovative
- Blends coded agents with low-code orchestration
- Uses deterministic BPMN for operational reliability
- Preserves human control in high-risk branches
- Demonstrates production-style emergency procurement governance

## Coding agents usage (bonus)
We used coding agents through UiPath for Coding Agents to accelerate:
- API service scaffolding
- Rule and risk-logic iteration
- Documentation and test-flow design

## Business impact
- Faster emergency procurement cycle time and fewer manual touches
- Better policy-risk triage and approval control
- Improved surge handling through prioritization recommendations
- Strong auditability from end-to-end orchestration

## Repository and setup
Include link to public GitHub repo and ensure README provides:
- Components used
- Setup steps
- Prerequisites
- How to run demo scenarios

## Demo video link
Add final YouTube/Vimeo/Youku URL here.

## Presentation deck link
Add public share link here.
