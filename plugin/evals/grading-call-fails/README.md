# Why this case relies on the grading call failing

The eval sandbox gives each run a throwaway home, so the `claude` that
`evaluate.sh` shells out to is either missing from PATH or not logged in. A real
grade cannot be produced inside a case. Whether the grader bands a session
correctly is what `session-calibration/calibrate.sh` measures, outside the
sandbox.

That limitation is what makes this case useful. The first run of it found the
skill filling the gap itself: `evaluate.sh` failed, the model ran `digest.py` by
hand, read the rubric, and wrote a scorecard with its own C on it. That grade
never went through the pipeline the bands were calibrated on. `SKILL.md` gained
a "When there is no scorecard" section, and the case has passed since.

If the sandbox ever passes credentials through, the grading call will succeed.
The judge accepts that too, provided the reply reports the band and the path
the script wrote, so the case stays correct either way.
