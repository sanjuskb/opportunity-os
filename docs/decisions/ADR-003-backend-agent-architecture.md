# ADR-003: Agent Orchestration with LangGraph

## Status
Accepted

## Context
The platform executes complex multi-step workflows: opportunity discovery, qualification filtering, resume tailoring, and portal interaction. Unconstrained autonomous agents can wander or hallucinate.

## Decision
Standardize on LangGraph to build deterministic, cyclic state machines with typed Pydantic tool contracts and explicit human approval checkpoints.

## Consequences
- **Positive:** Total control over state transitions, auditable event history, and native support for halting and resuming workflows.
- **Negative:** Requires upfront graph design and state schema definitions.
