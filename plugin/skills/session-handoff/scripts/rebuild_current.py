#!/usr/bin/env python3
"""rebuild_current.py — regenerate a handoff folder's CURRENT.md from its entries.

CURRENT.md is derived, never hand-edited: every run rebuilds it from scratch out
of `<handoff>/entries/*.md`, so two sessions that collide on it self-heal on the
next run. The write is a temp file plus a rename, and `entries/` is re-listed
immediately before the rename so a session that handed off while this was running
is not dropped from the index.

Standard library only, Python 3.8+, no network and nothing to install.

  rebuild_current.py <handoff-dir> <folder-root> [options]

Entries are named `<YYYY-MM-DD>_<HHMM>_<SESSION_ID>_<SLUG>.md` with frontmatter
keys session, workstream, date, window_start, previous_entry, and the `##`
sections the skill's draft step emits. A file that does not parse is an error,
not something to skip: a dropped entry is a lost workstream.
"""

import argparse
import datetime as dt
import os
import re
import sys
import tempfile

SECTIONS = [
    "Where things stand",
    "Decisions since last handoff",
    "Files created or changed",
    "Rescued this run",
    "Open threads and next steps",
    "Needs your check",
]

# Sections the index itself reads out of each entry.
STANDS = "Where things stand"
NEXT = "Open threads and next steps"
PATH_SECTIONS = ["Files created or changed", "Rescued this run"]

FRONTMATTER_KEYS = ["session", "workstream", "date", "window_start", "previous_entry"]

ENTRY_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{4})_(?P<session>[0-9A-Za-z]+)_(?P<slug>[0-9A-Za-z][0-9A-Za-z-]*)\.md$"
)
BACKTICKED_RE = re.compile(r"`([^`\n]+)`")

MAX_KEY_FILES = 10
MAX_UNINDEXED = 50
MAX_REBUILDS = 5


class EntryError(Exception):
    pass


def parse_entry(path):
    """Parse one entry file into a dict, or raise EntryError with the reason."""
    name = os.path.basename(path)
    m = ENTRY_RE.match(name)
    if not m:
        raise EntryError(
            "filename does not match <YYYY-MM-DD>_<HHMM>_<SESSION_ID>_<SLUG>.md"
        )

    try:
        stamp = dt.datetime.strptime(m.group("date") + m.group("time"), "%Y-%m-%d%H%M")
    except ValueError:
        raise EntryError("filename carries a date or time that is not a real moment")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except UnicodeDecodeError:
        raise EntryError("file is not valid UTF-8")

    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise EntryError("does not open with a `---` frontmatter block")
    try:
        close = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise EntryError("frontmatter block is never closed with `---`")

    front = {}
    for raw in lines[1:close]:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise EntryError("frontmatter line is not `key: value`: %r" % raw)
        key, value = raw.split(":", 1)
        key = key.strip()
        if key in front:
            raise EntryError("frontmatter repeats the key `%s`" % key)
        front[key] = value.strip()

    missing = [k for k in FRONTMATTER_KEYS if k not in front]
    if missing:
        raise EntryError("frontmatter is missing: %s" % ", ".join(missing))
    if front["session"] != m.group("session"):
        raise EntryError(
            "frontmatter session `%s` disagrees with the filename's `%s`"
            % (front["session"], m.group("session"))
        )
    if front["workstream"] != m.group("slug"):
        raise EntryError(
            "frontmatter workstream `%s` disagrees with the filename's `%s`"
            % (front["workstream"], m.group("slug"))
        )
    for key in ("date", "window_start"):
        if not front[key]:
            raise EntryError("frontmatter `%s` is empty" % key)

    sections = {}
    current = None
    for raw in lines[close + 1:]:
        if raw.startswith("## "):
            current = raw[3:].strip()
            if current in sections:
                raise EntryError("section `## %s` appears twice" % current)
            sections[current] = []
        elif current is not None:
            sections[current].append(raw)

    unknown = [s for s in sections if s not in SECTIONS]
    if unknown:
        raise EntryError(
            "has sections the index does not know how to read: %s"
            % ", ".join("## " + s for s in sorted(unknown))
        )
    absent = [s for s in SECTIONS if s not in sections]
    if absent:
        raise EntryError(
            "is missing sections: %s" % ", ".join("## " + s for s in absent)
        )

    return {
        "file": name,
        "stamp": stamp,
        "session": front["session"],
        "slug": front["workstream"],
        "front": front,
        "sections": {k: "\n".join(v).strip() for k, v in sections.items()},
        "text": text,
    }


def load_entries(entries_dir):
    """Parse every entry, reporting all failures together rather than the first."""
    if not os.path.isdir(entries_dir):
        sys.exit("rebuild_current.py: error: no entries directory at %s" % entries_dir)

    names = sorted(n for n in os.listdir(entries_dir) if not n.startswith("."))
    entries, problems = [], []
    for name in names:
        full = os.path.join(entries_dir, name)
        if not os.path.isfile(full):
            continue
        if not name.endswith(".md"):
            problems.append("%s: is not a .md entry" % name)
            continue
        try:
            entries.append(parse_entry(full))
        except EntryError as exc:
            problems.append("%s: %s" % (name, exc))

    if problems:
        sys.stderr.write(
            "rebuild_current.py: error: %d entr%s in %s could not be read, and an\n"
            "entry that cannot be read is a workstream that vanishes from the index.\n"
            "Fix these and run again; nothing has been written.\n\n"
            % (len(problems), "y" if len(problems) == 1 else "ies", entries_dir)
        )
        for problem in problems:
            sys.stderr.write("  %s\n" % problem)
        sys.exit(2)

    # Newest first; ties broken on session then filename so the order is stable.
    entries.sort(key=lambda e: (e["stamp"], e["session"], e["file"]), reverse=True)
    return entries


def group_by_slug(entries):
    """One group per slug — two sessions on the same workstream share a heading."""
    groups = {}
    for entry in entries:
        groups.setdefault(entry["slug"], []).append(entry)
    ordered = sorted(
        groups.items(),
        key=lambda kv: (kv[1][0]["stamp"], kv[0]),
        reverse=True,
    )
    return [(slug, group) for slug, group in ordered]


def relative_paths(entry, root_names):
    """Backticked path-like strings from an entry, made relative to the folder root."""
    found = []
    for section in PATH_SECTIONS:
        for raw in BACKTICKED_RE.findall(entry["sections"].get(section, "")):
            candidate = normalise_path(raw.strip(), root_names)
            if candidate and candidate not in found:
                found.append(candidate)
    return found


def normalise_path(raw, root_names):
    """Return raw as a path relative to the folder root, or None if it is not one."""
    for prefix in root_names:
        if raw == prefix:
            return None
        if raw.startswith(prefix.rstrip("/") + "/"):
            raw = raw[len(prefix.rstrip("/")) + 1:]
            break
    else:
        if raw.startswith("/"):
            # A container-side absolute path: ephemeral, and not ours to index.
            return None
    if raw.startswith("./"):
        raw = raw[2:]
    raw = raw.strip().rstrip("/")
    if not raw or raw.startswith("$") or (" " in raw and "/" not in raw):
        return None
    if "/" not in raw and not re.search(r"\.[A-Za-z0-9]{1,6}$", raw):
        return None
    return raw


def walk_root(root, skip_dirs):
    """Every visible file under the folder root, relative and sorted."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".")
            and (os.path.join(rel_dir, d) if rel_dir else d) not in skip_dirs
        )
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            rel = os.path.join(rel_dir, name) if rel_dir else name
            out.append(rel)
    return sorted(out)


def unindexed(root, entries, skip_dirs, skip_files):
    """Files in the folder that no entry names.

    Matching is per file and never per directory. Treating a directory as
    accounted for because one entry happened to mention one file inside it
    would hide precisely what this section exists to surface: work another
    session put in `reports/` or `notes/` and has not handed off yet, sitting
    beside files that are already indexed. The two failure directions are not
    equal — a file listed here that turns out to be covered costs the reader a
    glance, and a file missing from here is invisible until it is lost.
    """
    haystack = "\n".join(e["text"] for e in entries)
    missing = []
    for rel in walk_root(root, skip_dirs):
        if rel in skip_files:
            continue
        if rel in haystack:
            continue
        missing.append(rel)
    return missing


def render(root, entries, groups, dormant_cutoff, unindexed_files, account_bound):
    folder = os.path.basename(os.path.abspath(root)) or root
    out = []
    w = out.append

    w("# %s — session handoffs" % folder)
    w("")
    w(
        "`%s` is a connected folder worked in by more than one Claude session; this "
        "file is where to start, and `_Handoffs/entries/` holds the detail behind "
        "every line of it." % folder
    )
    w("")
    w(
        "Generated from the entries by `rebuild_current.py`. Edits made here are "
        "overwritten by the next handoff — correct an entry instead."
    )
    w("")

    active = [(s, g) for s, g in groups if g[0]["stamp"] >= dormant_cutoff]
    dormant = [(s, g) for s, g in groups if g[0]["stamp"] < dormant_cutoff]
    root_names = ["$ROOT", "${ROOT}", os.path.abspath(root), root]

    w("## Active workstreams")
    w("")
    if not active:
        w("None. Every workstream below has been dormant for 60 days or more.")
        w("")
    for slug, group in active:
        newest = group[0]
        sessions = []
        for entry in group:
            if entry["session"] not in sessions:
                sessions.append(entry["session"])
        w("### %s" % slug)
        w("")
        w("- Sessions: %s" % ", ".join("`%s`" % s for s in sessions))
        w(
            "- Last updated: %s, from `entries/%s`"
            % (newest["stamp"].strftime("%Y-%m-%d %H:%M"), newest["file"])
        )
        w("- Entries: %d" % len(group))
        w("")
        w("**Where it stands**")
        w("")
        w(newest["sections"][STANDS] or "_The entry left this section empty._")
        w("")
        w("**Next steps**")
        w("")
        w(newest["sections"][NEXT] or "_The entry left this section empty._")
        w("")
        paths = []
        for entry in group:
            for path in relative_paths(entry, root_names):
                if path not in paths:
                    paths.append(path)
        if paths:
            w("**Key files**, relative to the folder root")
            w("")
            for path in paths[:MAX_KEY_FILES]:
                w("- `%s`" % path)
            if len(paths) > MAX_KEY_FILES:
                w("- and %d more, named in the entries" % (len(paths) - MAX_KEY_FILES))
            w("")

    if dormant:
        w("## Dormant workstreams")
        w("")
        w("Untouched for 60 days or more. The entries are still in `entries/`.")
        w("")
        for slug, group in dormant:
            sessions = []
            for entry in group:
                if entry["session"] not in sessions:
                    sessions.append(entry["session"])
            w(
                "- **%s** — sessions %s, last updated %s, `entries/%s`"
                % (
                    slug,
                    ", ".join("`%s`" % s for s in sessions),
                    group[0]["stamp"].strftime("%Y-%m-%d"),
                    group[0]["file"],
                )
            )
        w("")

    w("## Present but not yet indexed")
    w("")
    if unindexed_files:
        w(
            "No entry accounts for these. They are most likely another session's work "
            "that has not been handed off yet. What state they are in is unknown from "
            "here — running `/session-handoff` in the session that owns them will give "
            "them an entry."
        )
        w("")
        for rel in unindexed_files[:MAX_UNINDEXED]:
            w("- `%s`" % rel)
        if len(unindexed_files) > MAX_UNINDEXED:
            w("- and %d more" % (len(unindexed_files) - MAX_UNINDEXED))
    else:
        w("Nothing. Every file in the folder is accounted for by an entry.")
    w("")

    w("## Recreate on a new account")
    w("")
    if account_bound:
        w(account_bound)
    else:
        w(
            "Nothing recorded yet. Scheduled tasks, connectors, skills and Project "
            "docs do not migrate with the folder; the next handoff should list them "
            "here, with the source each skill installs from."
        )
    w("")

    w("## Where the detail is")
    w("")
    w(
        "`entries/` holds one file per handoff, named "
        "`<date>_<time>_<session>_<workstream>.md`. %d entr%s across %d workstream%s."
        % (
            len(entries),
            "y" if len(entries) == 1 else "ies",
            len(groups),
            "" if len(groups) == 1 else "s",
        )
    )
    w("")
    return "\n".join(out)


def snapshot(entries_dir):
    """What `entries/` looks like right now — the concurrency check compares two."""
    state = []
    for name in sorted(os.listdir(entries_dir)):
        try:
            st = os.stat(os.path.join(entries_dir, name))
        except OSError:
            continue
        state.append((name, st.st_size, st.st_mtime_ns))
    return tuple(state)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="rebuild_current.py",
        description=(
            "Rebuild a handoff folder's CURRENT.md from every entry in entries/. "
            "The output is derived: it is safe to run at any time, and two sessions "
            "that collide on it self-heal on the next run."
        ),
        epilog=(
            "Entries are `<YYYY-MM-DD>_<HHMM>_<SESSION_ID>_<SLUG>.md` with "
            "frontmatter session, workstream, date, window_start, previous_entry, "
            "and the sections the handoff skill's draft step writes. An entry that "
            "does not parse aborts the run and names the file, because an entry "
            "silently skipped is a workstream lost from the index."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "handoff",
        help="the handoff directory, the one holding entries/ and .state/ (e.g. $ROOT/_Handoffs)",
    )
    parser.add_argument(
        "root",
        help="the connected folder root ($ROOT), used to list what no entry accounts for",
    )
    parser.add_argument(
        "--out",
        metavar="FILE",
        help="write somewhere other than <handoff>/CURRENT.md, for staging a commit",
    )
    parser.add_argument(
        "--account-bound",
        metavar="FILE",
        help=(
            "markdown for the 'Recreate on a new account' section "
            "(default: <handoff>/.state/account-bound.md when it exists)"
        ),
    )
    parser.add_argument(
        "--dormant-days",
        type=int,
        default=60,
        metavar="N",
        help="a workstream untouched for this long moves to the dormant list (default: 60)",
    )
    parser.add_argument(
        "--now",
        metavar="YYYY-MM-DD",
        help="treat this as today when deciding dormancy (default: the system date)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the index instead of writing it, changing nothing on disk",
    )
    args = parser.parse_args(argv)

    handoff = os.path.abspath(args.handoff)
    root = os.path.abspath(args.root)
    entries_dir = os.path.join(handoff, "entries")
    if not os.path.isdir(handoff):
        sys.exit("rebuild_current.py: error: no handoff directory at %s" % handoff)
    if not os.path.isdir(root):
        sys.exit("rebuild_current.py: error: no folder root at %s" % root)

    if args.now:
        try:
            now = dt.datetime.strptime(args.now, "%Y-%m-%d")
        except ValueError:
            sys.exit("rebuild_current.py: error: --now must be YYYY-MM-DD")
    else:
        now = dt.datetime.now()
    cutoff = now - dt.timedelta(days=args.dormant_days)

    account_file = args.account_bound or os.path.join(
        handoff, ".state", "account-bound.md"
    )
    account_bound = ""
    if os.path.isfile(account_file):
        with open(account_file, "r", encoding="utf-8") as fh:
            account_bound = fh.read().strip()
    elif args.account_bound:
        sys.exit("rebuild_current.py: error: no such file: %s" % account_file)

    out_path = os.path.abspath(args.out) if args.out else os.path.join(handoff, "CURRENT.md")

    # The handoff tree is the index's own bookkeeping, and the README is the
    # pointer the skill writes; neither is an unindexed file.
    skip_dirs = set()
    if handoff.startswith(root + os.sep):
        skip_dirs.add(os.path.relpath(handoff, root))
    skip_files = {"README.md"}
    if out_path.startswith(root + os.sep):
        skip_files.add(os.path.relpath(out_path, root))

    for attempt in range(MAX_REBUILDS):
        before = snapshot(entries_dir)
        entries = load_entries(entries_dir)
        groups = group_by_slug(entries)
        text = render(
            root,
            entries,
            groups,
            cutoff,
            unindexed(root, entries, skip_dirs, skip_files),
            account_bound,
        )

        if args.stdout:
            sys.stdout.write(text)
            return 0

        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(out_path) or ".", prefix=".CURRENT.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            # Re-list entries/ at the last possible moment: a session that handed
            # off while this was drafting must not be dropped from the index.
            if snapshot(entries_dir) != before:
                os.unlink(tmp)
                continue
            os.replace(tmp, out_path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

        print(
            "Wrote %s — %d entries, %d workstreams." % (out_path, len(entries), len(groups))
        )
        return 0

    sys.exit(
        "rebuild_current.py: error: entries/ kept changing under %d rebuilds; "
        "another session is writing right now. Run again in a moment." % MAX_REBUILDS
    )


if __name__ == "__main__":
    sys.exit(main())
