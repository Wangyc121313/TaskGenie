# TaskGenie Agent Architecture

## Core Runtime

TaskGenie now centers on a hand-rolled runtime under `apps/api/app/agent/`.

The runtime is intentionally split into:

- `planner`: converts user intent into structured plan artifacts
- `policy`: decides whether side-effecting steps require human confirmation
- `executor`: turns planned tasks into tool calls and executes them
- `trace_formatter`: exposes decision-level summaries to the frontend
- `runtime`: coordinates the full lifecycle

## Current Pattern

The current runtime uses `Plan-and-Execute`.

Flow:

1. analyze the input and load relevant user context
2. build a structured plan
3. convert the plan into formalized tool calls
4. pause for confirmation if the tool calls are side-effecting
5. execute the tool calls
6. append reflection notes and persist a trace summary

## Why Not LangGraph Yet

TaskGenie intentionally does not introduce LangGraph in this stage.

Reasoning:

- the current state graph is small and explicit
- the code benefits from lower abstraction overhead while the product is still evolving quickly
- it is easier to explain every runtime decision in interviews
- the runtime interfaces are now separated enough that migration to a graph framework remains possible

## Mapping To A Future LangGraph Migration

Current modules already map cleanly to graph concepts:

- `planner` -> planning node
- `policy` -> routing / branching node
- `executor` -> tool execution node
- `trace_formatter` -> summary node
- `confirmation` -> human-in-the-loop gate

This keeps the project framework-ready without adding framework complexity prematurely.
