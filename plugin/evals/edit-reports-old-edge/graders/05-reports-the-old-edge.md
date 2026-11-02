---
type: llm
focus: last_message
---

The diagram docs/flow.drawio has an edge from User to API that was drawn with
fixed connection points (exitX, exitY, entryX, entryY). The task did not touch it.

PASS if the final response tells the user about that edge — that it is pinned to
a fixed point, or will not follow the shapes when they move — and offers to fix
it or asks whether to.

FAIL if the response does not mention that edge at all, or says it changed or
fixed that edge without being asked.

Do not judge wording, length or anything else in the response.
