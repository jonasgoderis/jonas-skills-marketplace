# Why the cost is graded on the final reply

The first version of `states-the-cost` judged the whole trace, because the skill
said to state the cost *first* and runs did so mid-turn, before `--on`. The judge
failed a run that said, word for word, "roughly 6,000 input tokens per session on
Haiku" — it is handed the raw trace JSON, which opens with a long system blob,
and did not reliably find one sentence in it. A judge on `target: trace` is
the wrong instrument here, as it was for `cut-a-release`.

Another run switched it on without mentioning the cost at all, which is a real
miss. Both were fixed the same way: `SKILL.md` now asks for the cost to be
repeated in the reply that confirms the switch, since that is the one the user
reads, and the grader judges that reply.

In the sandbox `enable-hook.sh --on` usually fails: `CLAUDE_PLUGIN_DATA` is unset
and `~/.claude/evaluate-session` is not writable. The graders accept a run that
reports that honestly. What they check is that the switch went through
`enable-hook.sh`, that no settings or hooks file was edited, and that the user
heard the cost.
