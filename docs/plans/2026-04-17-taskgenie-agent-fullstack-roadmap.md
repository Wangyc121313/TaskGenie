# TaskGenie Agent + AI Full-Stack Roadmap

## Summary

This roadmap turns TaskGenie from an LLM-powered task utility into a portfolio project that can support both AI agent and AI full-stack job narratives.

The implementation priorities are:

1. formalize the backend into an explainable agent runtime
2. expose agent execution to users through a unified assistant UX
3. make tool, memory, and trace layers explicit enough for interviews
4. add minimal evals, CI, and docs so the project reads like an engineered system

## What Changed In This Iteration

- Added a unified backend agent runtime under `apps/api/app/agent/`
- Added `POST /ai/agent/run`, `GET /ai/agent/runs/{job_id}`, and `POST /ai/agent/runs/{job_id}/confirm`
- Added confirmation gating for side-effecting tool calls
- Added decision-level timeline traces and richer tool metadata
- Added a mobile `Assistant` surface and a `Profile` surface
- Added editable memory management and structured preference updates
- Added evaluation fixtures and GitHub Actions CI

## Interview Narrative

TaskGenie now supports a clearer explanation:

- The system uses a `Plan-and-Execute` agent pattern.
- It keeps human approval in front of high-impact writes.
- It maintains structured user preferences and long-term memory.
- It records both low-level execution events and high-level agent decisions.
- It keeps a hand-rolled runtime because the current state graph is small and explicit, while the interfaces remain migration-ready for frameworks like LangGraph later.

## Next Milestones

### 1. UX Hardening

- Refine the assistant tab interaction polish
- Replace remaining legacy modal-only AI flows with assistant-first flows
- Add schedule confirmation and richer timeline rendering

### 2. Eval Automation

- Add a regression runner for the eval datasets
- Track schema pass rate and tool execution rate over time
- Report eval summaries in CI

### 3. Portfolio Assets

- Record a 3-5 minute demo walkthrough
- Add screenshots and agent architecture diagrams to the README
- Prepare a concise “why not LangGraph yet” section for interviews
