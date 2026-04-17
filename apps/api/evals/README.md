# TaskGenie Agent Evals

This folder stores lightweight regression datasets for the portfolio version of TaskGenie.

The current eval coverage is intentionally small and local-first:

- `text_planning_dataset.json`: 20 goal-to-plan examples
- `image_task_dataset.json`: 10 image-to-task examples
- `memory_hit_dataset.json`: 10 memory retrieval examples

Suggested metrics:

- schema success rate
- planned task coverage
- tool execution success rate
- memory hit relevance

These files are designed for simple offline regression scripts and future CI hooks.
