---
type: tool_used
tool: Bash
input_match: 'evaluate\.sh\S*\s(?!.*--dry-run).*--transcript'
min: 0
max: 0
---

An evaluate.sh call with a transcript and without --dry-run is a real, paid grading call.
