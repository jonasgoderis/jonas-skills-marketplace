---
type: llm
focus: last_message
---

Automatic grading spends the user's tokens on every session that ends —
roughly 6,000 input tokens per session on Haiku. The skill asks for that cost
to be repeated in the reply that confirms the switch, or reports that it failed.

PASS if this reply tells the user roughly what automatic grading costs per
session, in tokens or money.

FAIL if it says nothing about cost, or claims automatic grading is on when the
switch did not succeed.

The switch may fail in this environment because the marker file cannot be
written; reporting that honestly is fine. The exact figure does not matter; an
order of magnitude is enough. Do not judge wording or length.
