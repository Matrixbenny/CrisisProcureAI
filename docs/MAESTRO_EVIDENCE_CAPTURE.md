# Maestro Evidence Capture (Track 2)

Use this to capture final proof for UiPath Maestro BPMN compliance.

## Required runs
1. Happy path run
2. Exception path run with explicit human approval

## Evidence checklist (must-have)
- BPMN canvas in Maestro showing task sequence and gateways
- Run history timeline from start to completion
- Human task screen during exception approval
- Agent/API task outputs in flow context
- Final completed state for both runs

## Actor proof mapping
- Human: approval task screenshot and completion timestamp
- Agent: compliance-risk and prioritization response evidence
- API/Robot: service task execution and handoff evidence
- Orchestration: Maestro timeline connecting all actors

## Capture order for speed
1. Open Maestro BPMN process canvas and capture
2. Trigger happy path run and capture timeline + completion
3. Trigger exception run and capture approval task + completion
4. Capture logs showing API/agent task invocation
5. Save assets in `assets/` with clear names

## File naming convention
- assets/maestro-canvas.png
- assets/run-happy-timeline.png
- assets/run-exception-timeline.png
- assets/human-approval-task.png
- assets/agent-api-task-output.png

## Submission insertion points
- Add screenshots to Devpost image gallery
- Reference evidence in README under Demo checklist
- Mention run IDs in docs/DEVPOST_SUBMISSION.md narrative
