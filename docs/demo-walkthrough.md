# TaskGenie Demo Walkthrough

## 3-5 Minute Flow

1. Open the Assistant tab.
2. Enter a vague goal such as “Plan my AI agent portfolio upgrades for this week”.
3. Show the resulting goal summary, planned tasks, timeline, and memory usage count.
4. Highlight that the run pauses for confirmation before creating tasks.
5. Confirm the run and show the created tasks.
6. Switch to the Profile tab and show stored preferences plus auto-extracted memories.
7. Run the image-to-task flow and show that the same agent runtime handles multimodal input.
8. Mention the CI workflow and eval fixtures in the repo.

## Talking Points

- “This is not a single prompt call. It is an explicit runtime with planner, policy, executor, and trace layers.”
- “High-impact writes are gated behind confirmation.”
- “The memory system is structured and user-editable.”
- “The project includes eval datasets and CI, so model and prompt changes are testable.”
- “I intentionally kept the runtime hand-rolled because the current graph is small, but I separated the interfaces so it can migrate to LangGraph later.”
