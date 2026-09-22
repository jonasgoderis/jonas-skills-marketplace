# Why this case asserts so little about the middle of the procedure

The skill's procedure has a check-in at step 3: propose the version level and
let the user correct it. A run that stops there, before the dry run, is
following the skill, not failing it — and in an eval there is no user to
answer, so the run ends.

That makes the dry run unassertable here. An earlier version of this case
required it and failed a compliant run; a `tool_order` grader keyed on
`--dry-run` failed the same way, because its "after" never happened.

What is left are the properties true of *every* compliant run, whenever it
stops: preflight ran first, the commits were read, no pull request was opened,
no version was edited by hand, and the notes it proposed reflect the diff.
