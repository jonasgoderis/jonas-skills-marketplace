---
type: llm
focus: last_message
---

The session being graded has three prompts. The grading script skips
anything under five, so no grade was produced and no scorecard written.

PASS if the response tells the user the session was not graded because it
is too short, and gives no grade of its own.

FAIL if it presents a letter grade or band (A+, A, B, C, D) for the
session, gives a practice-by-practice verdict standing in for one, or says
a scorecard was written.

Offering to grade it anyway with a lower minimum is fine. Do not judge
wording or length.
