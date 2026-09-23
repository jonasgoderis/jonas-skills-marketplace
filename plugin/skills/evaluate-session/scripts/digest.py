#!/usr/bin/env python3
"""Reduce a Claude Code transcript to a compact evidence digest.

The digest is what a grader sees, so this script is both the cost control and
the privacy boundary. It carries the user's own messages verbatim, because they
are the thing being graded, and reduces everything else to shape: which tools
ran, how often, what was edited, what was committed. Assistant prose, tool
output and file contents never leave this script.

Usage:
    digest.py --transcript <path.jsonl> [--project-dir DIR] [--max-chars N]
              [--secret-patterns FILE] [--min-turns N]

Writes JSON to stdout. Exits 3 when the session is too short to be worth
grading, and 4 when a secret pattern matched, in which case no digest is
emitted at all.
"""

import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
IDLE_GAP_MS = 5 * 60 * 1000  # a gap longer than this is the user away, not work

# User events that are machinery rather than something a person typed. The
# transcript replays history on resume, marks injected text, and carries the
# expanded body of every slash command as if the user had typed it.
NOT_A_PROMPT = (
    "<task-notification",
    "<scheduled-wakeup",
    "<background-task",
    "<local-command-caveat>",
    "[Request interrupted",
    "Base directory for this skill:",
)
COMMAND_RE = re.compile(r"<command-(?:name|message)>/?([^<]+)</command-")
COMMAND_ARGS_RE = re.compile(r"<command-args>([^<]*)</command-args>")
GIT_COMMIT_RE = re.compile(r"\bgit\s+(?:-[^\s]+\s+)*commit\b")
# Files are often written by shell redirection rather than the edit tools, and a
# detector that only watches Edit/Write reports a session as touching nothing.
SHELL_WRITE_RE = re.compile(r"(?:^|[^>|&\d])>>?\s*([^\s;|&<>()]+)|\btee\s+(?:-a\s+)?([^\s;|&<>()]+)")
# A shell command's text also contains redirections inside heredoc bodies and
# regex literals, so a match only counts when it looks like an actual path.
PLAUSIBLE_PATH_RE = re.compile(r"^[A-Za-z0-9._~][A-Za-z0-9._/~-]*$")
TEST_RE = re.compile(r"\b(test\.sh|pytest|npm\s+test|go\s+test|cargo\s+test|make\s+test)\b")


def load_patterns(path):
    pats = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        label, _, rx = line.partition("|")
        try:
            pats.append((label, re.compile(rx)))
        except re.error:
            continue
    return pats


def text_of(content):
    """Plain text of a message, or None when it is a tool result or empty."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                return None
            if block.get("type") == "text":
                return block.get("text") or ""
    return None


def iso(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def parse(transcript):
    seen = set()
    first_ts = last_ts = prev_ts = None
    active_ms = 0
    messages = []
    tools = {}
    sequence = []
    skills = []
    subagent_types = []
    files_edited = []
    commits = 0
    tests = 0
    compactions = 0
    assistant_turns = 0
    side_questions = 0
    context_sizes = []

    with open(transcript, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue

            uuid = e.get("uuid")
            if uuid:
                if uuid in seen:
                    continue  # resumed sessions replay their history
                seen.add(uuid)

            ts = e.get("timestamp")
            if ts:
                try:
                    ms = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
                except ValueError:
                    ms = None
                if ms is not None:
                    if first_ts is None:
                        first_ts = ms
                    if prev_ts is not None:
                        gap = ms - prev_ts
                        if 0 < gap < IDLE_GAP_MS:
                            active_ms += gap
                    prev_ts = last_ts = ms

            if e.get("isCompactSummary"):
                compactions += 1
                continue
            if e.get("isSidechain"):
                # A side question is asked deliberately to keep it out of the
                # main thread, so it is evidence of context hygiene rather than
                # noise. Counted, never read.
                if e.get("type") == "user":
                    side_questions += 1
                continue
            if e.get("isMeta"):
                continue

            kind = e.get("type")

            if kind == "user":
                body = text_of(e.get("message", {}).get("content"))
                if body is None:
                    continue
                body = body.strip()
                if not body or body.startswith(NOT_A_PROMPT):
                    continue
                m = COMMAND_RE.search(body)
                if m:
                    # Arguments are most of the signal. "/release-version 1.9.2"
                    # is a specific instruction; "/release-version" looks like an
                    # empty message and reads as a vague one.
                    args = COMMAND_ARGS_RE.search(body)
                    text = "/" + m.group(1).strip()
                    if args and args.group(1).strip():
                        text += " " + args.group(1).strip()
                    messages.append({"at": iso(prev_ts), "kind": "command", "text": text})
                else:
                    messages.append({"at": iso(prev_ts), "kind": "prompt", "text": body})
                continue

            if kind == "assistant":
                assistant_turns += 1
                u = e.get("message", {}).get("usage") or {}
                total_in = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) \
                    + (u.get("cache_creation_input_tokens") or 0)
                if total_in:
                    context_sizes.append(total_in)
                content = e.get("message", {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    name = block.get("name") or "?"
                    tools[name] = tools.get(name, 0) + 1
                    sequence.append(name)
                    inp = block.get("input") or {}
                    if name == "Skill" and inp.get("skill"):
                        skills.append(str(inp["skill"]))
                    elif name in ("Agent", "Task"):
                        subagent_types.append(str(inp.get("subagent_type") or "unspecified"))
                    elif name in ("Edit", "Write", "NotebookEdit"):
                        if inp.get("file_path"):
                            files_edited.append(str(inp["file_path"]))
                    elif name == "Bash":
                        cmd = str(inp.get("command") or "")
                        if GIT_COMMIT_RE.search(cmd):
                            commits += 1
                        if TEST_RE.search(cmd):
                            tests += 1
                        for a, b in SHELL_WRITE_RE.findall(cmd):
                            target = a or b
                            if not target or not PLAUSIBLE_PATH_RE.match(target):
                                continue
                            if "/" not in target and "." not in target:
                                continue  # a bare word is heredoc text, not a path
                            files_edited.append(target)

    return {
        "first_ts": first_ts, "last_ts": last_ts, "active_ms": active_ms,
        "messages": messages, "tools": tools, "sequence": sequence,
        "skills": skills, "subagent_types": subagent_types,
        "files_edited": files_edited, "commits": commits, "tests": tests,
        "compactions": compactions, "assistant_turns": assistant_turns,
        "side_questions": side_questions, "context_sizes": context_sizes,
    }


def _project_relative(path, project_dir):
    """Keep project files only, as relative paths.

    Two reasons to drop the rest. Scratch files under /tmp are not the work
    being graded, and an absolute path carries the machine's directory layout
    into text that gets sent to a model.
    """
    if not project_dir:
        return None
    try:
        resolved = Path(path).resolve()
        rel = str(resolved.relative_to(Path(project_dir).resolve()))
    except (ValueError, OSError):
        return None
    # A shell redirection target that matches no real file is text that merely
    # looked like a path — a variable name, a fragment of a regex.
    return rel if resolved.exists() else None


def structural(project_dir):
    """Facts about the project, for the practices no transcript can show."""
    if not project_dir:
        return {"checked": False}
    root = Path(project_dir)
    if not root.is_dir():
        return {"checked": False}

    claude_md = root / "CLAUDE.md"
    rules_here = root / ".claude" / "rules"
    # Rules are commonly kept at user level and symlinked from a dotfiles repo,
    # so a project-only check reports "absent" for someone doing this well.
    rules_home = Path.home() / ".claude" / "rules"
    skills_root = root / "plugin" / "skills"
    if not skills_root.is_dir():
        skills_root = root / ".claude" / "skills"
    skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()] if skills_root.is_dir() else []

    body = claude_md.read_text(encoding="utf-8", errors="replace") if claude_md.is_file() else ""
    # BP-02 is about context being split and pointed at, not about filenames.
    # Counting files whose name contains "claude" scored a properly split
    # docs/testing.md as unsplit.
    referenced = {m for m in re.findall(r"[\w./-]+\.md", body)
                  if (root / m).is_file() and m.lower() != "claude.md"}

    return {
        "checked": True,
        "claude_md": {
            "present": claude_md.is_file(),
            "lines": len(body.splitlines()),
            "references_other_files": sorted(referenced),
        },
        "rules_files": {
            "project": len(list(rules_here.glob("*.md"))) if rules_here.is_dir() else 0,
            "user": len(list(rules_home.glob("*.md"))) if rules_home.is_dir() else 0,
        },
        # BP-14: skills using progressive disclosure.
        "skills": {
            "count": len(skill_dirs),
            "with_references": len([d for d in skill_dirs if (d / "references").is_dir()]),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--project-dir")
    ap.add_argument("--max-chars", type=int, default=60000)
    ap.add_argument("--min-turns", type=int, default=5)
    ap.add_argument("--secret-patterns")
    args = ap.parse_args()

    if not os.path.isfile(args.transcript):
        print(f"digest: no such transcript: {args.transcript}", file=sys.stderr)
        return 2

    d = parse(args.transcript)
    prompts = [m for m in d["messages"] if m["kind"] == "prompt"]
    if len(prompts) < args.min_turns:
        print(f"digest: {len(prompts)} prompt(s), below the {args.min_turns} needed "
              "to say anything useful", file=sys.stderr)
        return 3

    # Privacy gate. A transcript is exactly the kind of file that ends up holding
    # a pasted token, so a match stops the digest rather than annotating it.
    default_patterns = Path(__file__).resolve().parent.parent / "assets" / "secret-patterns.txt"
    pattern_file = args.secret_patterns or default_patterns
    findings = []
    if Path(pattern_file).is_file():
        for label, rx in load_patterns(pattern_file):
            for i, m in enumerate(d["messages"], 1):
                if rx.search(m["text"]):
                    findings.append({"label": label, "message": i})
                    break
    if findings:
        print("digest: refusing to emit — the session's own messages match "
              + ", ".join(sorted({f['label'] for f in findings}))
              + ". Nothing was written.", file=sys.stderr)
        return 4

    # Number before truncating. Renumbering afterwards makes every citation in
    # the report point at a different turn than the one it describes.
    for n, m in enumerate(d["messages"], 1):
        m["i"] = n

    # Truncate by whole messages from the oldest end, and say so.
    dropped = 0
    total = sum(len(m["text"]) for m in d["messages"])
    while total > args.max_chars and len(d["messages"]) > 1:
        total -= len(d["messages"].pop(0)["text"])
        dropped += 1

    subagent_dir = Path(args.transcript).with_suffix("") / "subagents"
    wall_ms = (d["last_ts"] - d["first_ts"]) if d["first_ts"] and d["last_ts"] else 0

    digest = {
        "schema": SCHEMA,
        "session": {
            "id": Path(args.transcript).stem,
            "project": os.path.basename(args.project_dir) if args.project_dir else None,
            "started": iso(d["first_ts"]),
            "ended": iso(d["last_ts"]),
            "wall_minutes": round(wall_ms / 60000, 1),
            "active_minutes": round(d["active_ms"] / 60000, 1),
            "user_prompts": len(prompts),
            "slash_commands": len([m for m in d["messages"] if m["kind"] == "command"]),
            "assistant_turns": d["assistant_turns"],
        },
        "truncated": {"messages_dropped": dropped},
        "messages": d["messages"],
        # Named for what it is. Every entry below is something the ASSISTANT
        # chose to do. The user cannot launch a subagent, run a test or make a
        # commit, so none of it is evidence of what the user did — only of what
        # happened after they asked.
        "assistant_activity": {
            "tools": dict(sorted(d["tools"].items(), key=lambda kv: -kv[1])),
            "tool_calls": sum(d["tools"].values()),
            # Repeated identical runs are the signal for work that wants a script.
            "repeated_tool_runs": {k: v for k, v in sorted(
                collections.Counter(
                    " > ".join(d["sequence"][i:i + 3])
                    for i in range(max(0, len(d["sequence"]) - 2))
                ).items(), key=lambda kv: -kv[1])[:5] if v >= 3},
            "skills_invoked": sorted(set(d["skills"])),
            "subagents": {
                "launched": len(d["subagent_types"]),
                "types": sorted(set(d["subagent_types"])),
                "transcripts_on_disk": len(list(subagent_dir.glob("*.jsonl")))
                if subagent_dir.is_dir() else 0,
            },
            "files_edited": sorted({r for r in (_project_relative(f, args.project_dir)
                                            for f in d["files_edited"]) if r}),
            "commits": d["commits"],
            "test_runs": d["tests"],
            "compactions": d["compactions"],
        },
        # Things the user did, as opposed to things done on their behalf.
        "user_activity": {
            "side_questions": d["side_questions"],
        },
        # Context pressure, which is what BP-01 is actually about.
        "context": {
            "peak_input_tokens": max(d["context_sizes"]) if d["context_sizes"] else 0,
            "final_input_tokens": d["context_sizes"][-1] if d["context_sizes"] else 0,
            "compactions": d["compactions"],
        },
        "structural": structural(args.project_dir),
    }
    json.dump(digest, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
