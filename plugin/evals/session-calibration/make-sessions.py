#!/usr/bin/env python3
"""Build two synthetic sessions with known ground truth, and a project to hold them.

`evaluate-session` grades how a session was driven, and every real transcript on
this machine was driven by someone who already knows how. That gives the grader
no evidence it can still mark a session down — the failure mode of a rubric whose
bands resolve upward is that everything becomes an A, and nothing in the repo
would notice.

So the calibration supplies both ends. `bad` is a session that cost itself five
episodes, each one explained by words the user actually typed. `ordinary` is the
same project driven properly. The fixture project is deliberately healthy —
CLAUDE.md present and split, rules on disk — so the structural practices are
identical across the two and cannot be what moves the grade.

The transcripts are generated rather than committed because the shape is the
point: reading this file tells you what each session is meant to demonstrate,
where 800 lines of JSON would not.
"""

import argparse
import json
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

START = datetime(2026, 9, 19, 9, 2, 0, tzinfo=timezone.utc)

# The files the sessions touch. digest.py drops any edit whose path does not
# resolve inside the project, so these have to exist for the fixture to record
# that anything was edited at all.
SOURCES = [
    "src/server.js", "src/auth.js", "src/cache.js", "src/db.js",
    "src/rateLimiter.js", "src/middleware/rateLimit.js",
    "src/routes/dashboard.js", "src/export/csv.js", "test/api.test.js",
]

CLAUDE_MD = """\
# Shipping tracker

Node service tracking shipment state. See `docs/architecture.md` for the layout
and `docs/testing.md` for how the suite is run.

Rate limiting stays in the middleware layer. Routes do not rate-limit themselves.
"""


class Tape:
    """Accumulates transcript events in the shape Claude Code writes them."""

    def __init__(self):
        self.events = []
        self.t = START
        self.ctx = 18000

    def user(self, text, gap=1.0):
        self.t += timedelta(minutes=gap)
        self._add({"type": "user", "message": {"role": "user", "content": text}})

    def assistant(self, tools=(), gap=0.4, grow=900):
        self.t += timedelta(minutes=gap)
        self.ctx += grow
        content = [{"type": "text", "text": "..."}]
        content += [{"type": "tool_use", "id": str(_uuid.uuid4()), "name": n, "input": i}
                    for n, i in tools]
        self._add({"type": "assistant", "message": {
            "role": "assistant", "content": content,
            "usage": {"input_tokens": 4, "cache_read_input_tokens": self.ctx,
                      "cache_creation_input_tokens": 0, "output_tokens": 600}}})
        # Tool results arrive as user events. digest.py drops them; they are here
        # so the fixture exercises that path rather than assuming it.
        for _ in tools:
            self.t += timedelta(seconds=12)
            self._add({"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": str(_uuid.uuid4()), "content": "ok"}]}})

    def compact(self):
        self.t += timedelta(seconds=30)
        self.ctx = 22000
        self._add({"type": "user", "isCompactSummary": True,
                   "message": {"role": "user", "content": "<summary>...</summary>"}})

    def _add(self, event):
        event["uuid"] = str(_uuid.uuid4())
        event["timestamp"] = self.t.isoformat().replace("+00:00", "Z")
        self.events.append(event)

    def write(self, path):
        Path(path).write_text(
            "".join(json.dumps(e) + "\n" for e in self.events), encoding="utf-8")


def read(p):  return ("Read", {"file_path": p})
def edit(p):  return ("Edit", {"file_path": p})
def grep(q):  return ("Grep", {"pattern": q})
def bash(c):  return ("Bash", {"command": c})


def bad(root):
    """Five costs, each traceable to something the user typed.

    Every one of them is quotable, which is what the rubric requires before a
    cost may be charged to the user: an episode where the missing information
    was theirs to give and you can name the words that were missing.

      message 3   a convention held but never stated, so the work is undone
      message 5   a reversal that discards the export work just finished
      message 7   the diagnosis injected at message 6 was wrong
      message 10  approval at message 9 without looking at what was approved
      message 14  an instruction ambiguous enough to be read the other way
    """
    t = Tape()
    s = lambda p: f"{root}/{p}"

    t.user("can you clean up the shipping tracker app? it's got a lot of issues", gap=0)
    t.assistant([grep("TODO"), read(s("src/server.js")), read(s("src/auth.js"))], grow=6000)
    t.assistant([read(s("src/cache.js")), read(s("src/middleware/rateLimit.js"))], grow=5200)

    t.user("yeah just do whatever you think", gap=3)
    t.assistant([edit(s("src/server.js")), edit(s("src/middleware/rateLimit.js"))], grow=4800)
    t.assistant([edit(s("src/rateLimiter.js")), bash("rm src/middleware/rateLimit.js")], grow=4400)

    t.user("no not like that. I wanted the rate limiter to stay in the middleware layer, "
           "we have a whole convention around that. put it back", gap=11)
    t.assistant([bash("git checkout src/middleware/rateLimit.js"), edit(s("src/server.js"))], grow=4100)
    t.assistant([edit(s("src/middleware/rateLimit.js"))], grow=3000)

    t.user("also while you're in there can you add the CSV export thing", gap=4)
    t.assistant([read(s("src/routes/dashboard.js")), edit(s("src/export/csv.js"))], grow=5200)
    t.assistant([edit(s("src/export/csv.js")), edit(s("src/server.js"))], grow=4600)

    t.user("actually forget the CSV for now, do the dashboard first", gap=6)
    t.assistant([bash("git checkout src/export/csv.js"), read(s("src/routes/dashboard.js"))], grow=4900)
    t.assistant([edit(s("src/routes/dashboard.js"))], grow=3800)

    t.user("the dashboard endpoint is slow. it's definitely a caching problem, "
           "just fix the cache", gap=9)
    t.assistant([read(s("src/cache.js")), edit(s("src/cache.js"))], grow=5400)
    t.assistant([edit(s("src/cache.js")), bash("node -e 'require(\"./src/cache.js\")'")], grow=4200)

    t.user("hmm still slow. ok it wasn't the cache. look properly this time", gap=8)
    t.assistant([grep("await"), read(s("src/routes/dashboard.js")), read(s("src/db.js"))], grow=6600)
    t.assistant([edit(s("src/routes/dashboard.js")), edit(s("src/db.js"))], grow=4700)

    t.user("ok", gap=5)
    t.assistant([read(s("src/db.js"))], grow=2600)

    t.user("fine, ship it", gap=2)
    t.assistant([bash("git add -A"), bash("git status")], grow=2800)

    t.user("wait, what did you change in auth.js? I never asked you to touch auth", gap=3)
    t.assistant([bash("git diff src/auth.js"), read(s("src/auth.js"))], grow=4300)
    t.assistant([bash("git checkout src/auth.js")], grow=2200)

    t.user("ugh this is getting long. anyway can you also look at why the tests are flaky", gap=14)
    t.assistant([read(s("test/api.test.js")), bash("npm test")], grow=7200)
    t.assistant([read(s("test/api.test.js")), edit(s("test/api.test.js"))], grow=5100)

    t.compact()

    t.user("just run the whole thing again and tell me what breaks", gap=4)
    for _ in range(4):
        t.assistant([bash("npm test"), read(s("test/api.test.js")), edit(s("test/api.test.js"))],
                    grow=6200)

    t.user("can you make the dashboard table match the spec", gap=7)
    t.assistant([read(s("src/routes/dashboard.js")), edit(s("src/routes/dashboard.js"))], grow=5000)

    t.user("no, I said the ORDER of the columns, not the names. change them back", gap=6)
    t.assistant([edit(s("src/routes/dashboard.js"))], grow=3400)
    t.assistant([edit(s("src/routes/dashboard.js"))], grow=3100)

    t.user("ok whatever, that's enough for today", gap=5)
    t.assistant([], grow=1200)
    return t


def ordinary(root):
    """The same project driven properly: scoped, held to one subject, iterated,
    verified before approval, and checkpointed to disk before stopping.

    Not a showpiece. It is what a competent hour looks like, and it is here so a
    grade on `bad` means something — a rubric that marks both the same has
    measured nothing.
    """
    t = Tape()
    s = lambda p: f"{root}/{p}"

    t.user("The dashboard endpoint GET /api/shipments takes ~4s. I want it under 500ms. "
           "Don't change the response shape — the mobile client depends on it. "
           "Start by telling me where the time goes; don't change anything yet.", gap=0)
    t.assistant([read(s("src/routes/dashboard.js")), read(s("src/db.js")), grep("await")], grow=6200)
    t.assistant([read(s("src/cache.js"))], grow=3000)

    t.user("That matches what I saw. Do the N+1 fix only — leave the cache alone for now, "
           "I want to see what the query change buys on its own.", gap=6)
    t.assistant([edit(s("src/db.js")), edit(s("src/routes/dashboard.js"))], grow=4600)
    t.assistant([bash("npm test")], grow=3400)

    t.user("Show me the diff before anything else, then run the api tests.", gap=4)
    t.assistant([bash("git diff"), bash("npm test")], grow=4200)

    t.user("Good. Commit that on its own so we can measure it, message in our usual style.", gap=5)
    t.assistant([bash("git add src/db.js src/routes/dashboard.js"),
                 bash("git commit -m 'Collapse the per-shipment lookup into one query'")], grow=3100)

    t.user("Now write what we found about the query path into docs/perf-notes.md — "
           "the numbers before and after, and why the cache was not the cause. "
           "Short, bullets, for whoever picks this up next.", gap=7)
    t.assistant([edit(s("docs/perf-notes.md")), bash("npm test")], grow=4000)

    t.user("Second para reads like marketing. Cut it to the measurement and drop the adjectives.", gap=5)
    t.assistant([edit(s("docs/perf-notes.md"))], grow=2400)

    t.user("Better. Commit the notes, then stop — the cache question is a separate session.", gap=4)
    t.assistant([bash("git add docs/perf-notes.md"),
                 bash("git commit -m 'Record the query-path findings'")], grow=2600)
    return t


def build_project(root):
    """A healthy project, on purpose.

    The structural practices read the filesystem, so if the fixture project were
    a mess both sessions would carry the same structural complaints and a low
    grade on `bad` would no longer prove the *driving* was what moved it.
    """
    root = Path(root)
    for rel in SOURCES:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("// placeholder for the calibration fixture\n", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "rules").mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(CLAUDE_MD, encoding="utf-8")
    (root / "package.json").write_text('{"name":"shipping-tracker","version":"0.1.0"}\n', encoding="utf-8")
    for rel, head in [("docs/architecture.md", "# Architecture"),
                      ("docs/testing.md", "# Testing"),
                      ("docs/perf-notes.md", "# Performance notes"),
                      (".claude/rules/commits.md", "# Commit style"),
                      (".claude/rules/review.md", "# Review rules")]:
        (root / rel).write_text(head + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="directory to build the fixture in")
    args = ap.parse_args()

    out = Path(args.out)
    project = out / "shipping-tracker"
    build_project(project)
    bad(str(project)).write(out / "bad-session.jsonl")
    ordinary(str(project)).write(out / "ordinary-session.jsonl")
    print(project)


if __name__ == "__main__":
    main()
