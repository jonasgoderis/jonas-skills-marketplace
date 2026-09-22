---
type: llm
focus: last_message
---

The branch under release has four commits: two features (a greeting, and a
parting message), one fix for a trailing newline that a commit on this same
branch had just broken, and one README typo correction.

The prompt asked for the proposed release notes, so they should be here.
Judge only those notes.

PASS if both of these hold:

1. The notes cover the new behaviour completely — both the greeting and the
   parting message are presented as new in this release. Describing either one
   as pre-existing is wrong: both arrive on this branch.
2. The README typo does not appear as an entry. It is not a change for anyone
   using the project.

Ignore everything else. In particular, do not fail the response for omitting
the trailing-newline fix — that fix repairs a commit from the same branch and
leaving it out is correct. Do not judge wording, formatting or section names.
