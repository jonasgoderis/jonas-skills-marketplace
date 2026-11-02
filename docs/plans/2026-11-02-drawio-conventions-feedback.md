# drawio-conventions: triage of field feedback

Date: 2026-11-02

Another Claude session used the `drawio-conventions` skill on two real diagrams.
It then proposed 13 improvements. This document says which ones fit the skill,
and why.

The skill is published software. So each suggestion is judged on one question:
does it help every user, or only the diagram in front of that session?

## Summary

| # | Suggestion | Verdict |
| --- | --- | --- |
| 1 | Colour per flow on edges, when a legend explains it | Take |
| 2 | `whiteSpace=nowrap` on icon labels | Take |
| 3 | 10–20 px spacing inside a stacked list without edges | Take |
| 4 | Allow moving a label along its own line (`mxGeometry x`) | Take |
| 5 | Line up the last waypoint with the target centre | Take, as a short hint |
| 6 | Protect user edits when a generator script exists | Take (data-loss risk) |
| 7 | Warn when the file is open in draw.io | Take, with the draft file (`.dtmp`), not the backup file |
| 8 | Re-read the file from disk after writing | Take, folded into checklist D |
| 9 | Rules for multi-tab files | Take |
| 10 | `references/icons-azure.md` with checked icon paths | Change: a script that checks any icon path |
| 11 | `scripts/` with a checklist script and a render script | Take the checklist script. Render script is optional |
| 12 | Numbered steps on edges, labels at most 3 lines | Take the 3-line limit. Numbering goes in the house style |
| 13 | Rules for group frames | Take: real containers (decided) |

## Notes per suggestion

**1. Edge colour.** The house style makes every edge grey (`#999999`). A diagram
with several flows needs a colour per flow, so the earlier session had to break
the rule. Add: grey is the default, and a colour per flow is allowed when a
legend on the page explains each colour. Checklist item 5 must accept this.

**2. Icon labels.** The table sets `whiteSpace=wrap` on every vertex. An icon's
label sits under the picture, and wrapping limits it to the icon width (often
64 px). The result is a narrow stack of single words. Icons should use
`whiteSpace=nowrap`.

**3. Stacked lists.** The 80 px minimum exists so that a label on an edge has
room. A stack of queue boxes or a list of steps has no edges between its items.
So the reason for the rule does not apply there.

**4. Label position.** On an edge label, `mxGeometry x` (from -1 to 1) moves the
label along its own line. The `y` value and the `offset` point move it off the
line. The current text bans "an offset", which an agent can read as a ban on
`x` too. Say which one is allowed.

**5. Waypoints.** The claim is that a last waypoint off the target's centre line
makes draw.io add a small zigzag. This is plausible with the orthogonal router
and no fixed points, but I did not test it. One sentence of guidance costs
little.

**6. Generator scripts.** If a script generated the `.drawio` file, the user may
have moved shapes in draw.io since. Regenerating would then silently delete
their work. Before regenerating, compare the file on disk with the script
output. Copy any differences into the script first. This is the most important
suggestion, because the loss is invisible until later.

**7. File open in draw.io.** The draw.io desktop app can save its open copy over
a file that was just written. A warning prevents that. The suggestion says the
sign is a hidden `.$<name>.drawio.bkp` file next to the diagram. That is wrong.
The draw.io desktop source (`src/main/electron.js` in the app bundle) writes the
`.bkp` file on every save and never deletes it. The real sign of an open file
with unsaved work is the draft file `.$<name>.drawio.dtmp`. The skill uses the
draft file.

**8. Verify after writing.** Checklist D already says "run this over the final
XML, not over your memory". Make it explicit that this means reading the file
back from disk. A checksum is not needed.

**9. Multi-tab files.** Each `<diagram>` needs a unique `id` and `name`. Keep the
tab order. A new tab goes before `</mxfile>`. This belongs in the File format
section of the house style or in rule text, as it is a format rule.

**10. Azure icons.** See the section below.

**11. Scripts.** The repo's own guidance says that deterministic work goes in
`scripts/`. Checklist D is a fixed set of text checks. Most of them (items 1–4,
6, part of 7, and the file format) can run as a script. That makes the
checklist reliable instead of manual. A render script is useful for a visual
check, but only works when draw.io desktop is installed (`draw.io -x -f png`).
It must fail gracefully without it. The skill description then changes: it no
longer "does not validate". The eval case `drawio-export-png` (exporting a
diagram for a README) stays a near miss. Rendering for the agent's own check is
different from exporting for the user.

**12. Long labels and numbering.** A limit of 3 lines per label, with longer
text moved into a note, is general. It fixes the overlaps from the earlier
session. Numbering steps (1, 2, 3, with 6a and 6b for parallel steps) suits flow
diagrams only. It is a style choice, so it belongs in `references/house-style.md`.

**13. Group frames.** Two options:

- Real containers: the children get `parent="<group id>"`. Moving the group moves
  everything in it. Coordinates of children become relative to the group. Edges
  between groups need the right `parent`, and the "icons after edges" rule works
  per parent.
- Plain dashed rectangles: drawn first, so everything else is on top. Simple,
  but moving the frame leaves its contents behind.

## The Azure icon suggestion, explained

draw.io ships with picture libraries for Azure, AWS, GCP and others. A diagram
uses such a picture through a style like
`shape=image;image=img/lib/azure2/app_services/Search_Services.svg;`. That path
points to an SVG file inside draw.io itself.

If the path is wrong, draw.io shows an empty box. There is no error. This is
the same failure as a wrong style key. The earlier session guessed
`Cognitive_Search.svg` for Azure AI Search, which does not exist.

I checked the installed draw.io app. Its bundle (`app.asar`) contains 704 Azure
icons under `img/lib/azure2/`. `app_services/Search_Services.svg` is there, and
no `Cognitive_Search.svg` exists anywhere. So the claim is correct.

A hand-written list of Azure paths has two problems. It only helps Azure
diagrams. And it goes out of date when draw.io renames icons. A better fit is a
script that checks every `image=img/lib/...` path in a file against the
installed draw.io app, or against the draw.io GitHub repository when the app is
not installed. That works for every cloud vendor and stays current.

## Layout rules added after review

After the first diagrams with the new version, four more layout problems came
up. Each one is now a rule in `references/house-style.md`, and the first two
are also warnings in the script.

- **Jogs in lines that could be straight.** Two connected shapes must line up
  by their centres, not their tops. An icon of 64 px next to a box of 60 px with
  the same `y` is 2 px off, and draw.io then bends the line.
- **Crossings without need.** Targets follow the order of their sources. The
  script warns when two edges swap order between their ends.
- **More room.** The minimum gap between shapes is now 120 px, up from 80 px.
- **A straight end before the arrow head.** Every edge gets
  `targetJettySize=30`. draw.io's orthogonal router reads this key for the
  target end (checked in its source). It ignores it on edges with waypoints, so
  the last waypoint stays at least 30 px from the target.

## Eval results

Three full runs of the 11 `drawio-conventions` cases, 3 runs each.

| Run | Result | What changed after it |
| --- | --- | --- |
| 1 | 9 of 11 cases at 100% | Agents spent all their turns searching the draw.io app for AWS stencil names. Added `--find` to the script. |
| 2 | 10 of 11 at 100% | Grader `04-icons-after-edges` ignored the parent, so icons in a group container failed it. Made it compare parents. `--find` now prints a full style string and takes several terms. |
| 3 | 11 of 11 at 100% | — |

Model `claude-sonnet-5`, judge `claude-haiku-4-5-20251001`, as pinned in
`scripts/eval.sh`.
