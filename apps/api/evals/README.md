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

These files are designed for a simple local runner and CI smoke checks.

## Run Locally

From `apps/api`:

```bash
python evals/run_evals.py --mode offline
```

This writes a summary file to:

`evals/results/latest.json`

Current offline coverage:

- `text_planning`: dataset/schema readiness checks
- `image_task`: dataset/schema readiness checks
- `memory_hit`: local retrieval quality check against seeded memories

The runner also emits structured eval log events through the same logging pipeline used by agent runs.
