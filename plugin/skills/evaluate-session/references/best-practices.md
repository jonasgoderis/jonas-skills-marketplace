# Working well with Claude — the practice catalogue

Nineteen practices, grouped into five themes. Each has a stable identifier,
`BP-01` through `BP-19`, which is the contract: a scorecard cites the number, and
the number is what you look up here. Once published, an identifier never changes
meaning — a practice that is retired keeps its number and is marked retired rather
than reused.

Every entry carries an **observability** line. It says whether the practice can be
seen in a session transcript at all, which is what keeps a grade honest: a
practice the evidence cannot show is reported as unobservable rather than counted
against anyone.

- **Direct** — visible in what the user typed and what happened next.
- **Indirect** — inferable from signals, but not proof.
- **Structural** — a property of the project and its configuration, not of any one
  session. Checked by reading the filesystem, never guessed.

## Contents

**Context and scope** — [BP-01](#bp-01) · [BP-02](#bp-02) · [BP-03](#bp-03) · [BP-04](#bp-04) · [BP-05](#bp-05)
**Asking well** — [BP-06](#bp-06) · [BP-07](#bp-07) · [BP-08](#bp-08) · [BP-09](#bp-09) · [BP-10](#bp-10) · [BP-11](#bp-11)
**Delegation and determinism** — [BP-12](#bp-12) · [BP-13](#bp-13) · [BP-14](#bp-14)
**Trust** — [BP-15](#bp-15) · [BP-16](#bp-16) · [BP-17](#bp-17) · [BP-18](#bp-18)
**Setup** — [BP-19](#bp-19)

---

# Context and scope

## BP-01 — Watch the context, hand off before it rots

A long conversation degrades. Attention is not spread evenly across a large
window, so early decisions get buried under later detail, and the model starts
re-asking things that were settled an hour ago. Cost rises the whole time,
because every turn re-sends the entire history.

The failure mode is that this is gradual. There is no moment where the session
announces it has gone bad — the answers just get vaguer, and by the time it is
obvious, the useful reasoning is already buried.

**Doing it well:** notice the signals — repeated questions, forgotten decisions,
answers that drift from what was agreed — and end the session deliberately rather
than pushing through. Distil what matters into a file, clear, and start again
from the briefing instead of the transcript.

**Observability:** Indirect. Turn count, session duration, compaction events and
whether a handover file was written are all visible; whether the session
*should* have been ended earlier is a judgement on top of those.

## BP-02 — Split project context across files

A single large instructions file is loaded in full at the start of every session,
whether or not any of it applies to the task. Everything in it competes for
attention with the actual question.

Splitting by area fixes both problems at once: the always-relevant rules stay in
the root file, and the area-specific detail sits in separate files that are read
when that area is in play.

**Doing it well:** the root instructions file holds what is true everywhere.
Detail that only matters for one part of the system — a test strategy, an API's
conventions, a deployment procedure — lives in its own file and is pointed at
rather than inlined.

**Observability:** Structural. Read from the project layout.

## BP-03 — Break big tasks into small, checkable steps

One giant instruction gives you a single chance to be right and nowhere to
intervene. A sequence of scoped steps gives a checkpoint after each one, so a
wrong turn costs one step rather than a whole session's work.

This is also the cheapest correctness mechanism available. Reviewing a small
change is quick; reviewing a large one is work people skip.

**Doing it well:** ask for something with a visible result, look at it, then ask
for the next thing. Where the shape of the work is unclear, agree the plan first
and execute it in pieces.

**Observability:** Direct.

## BP-04 — One session, one subject

Mixing unrelated topics in one conversation spends tokens re-sending history
irrelevant to the current question, and measurably degrades instruction
following. A narrow scope is the single most reliable lever on output quality.

**Doing it well:** one conversation per subject. When a genuinely different topic
comes up, start somewhere else rather than appending it.

**Observability:** Direct. Topic drift across user messages is visible.

## BP-05 — Checkpoint knowledge to disk, not to the conversation

The conversation is volatile and the filesystem is not. Status, decisions and
open questions held only in context are lost at the next clear, compaction or
crash — and they are exactly the things most expensive to reconstruct.

**Doing it well:** keep todos, decisions and current status in files. Commit at
points where the work is coherent, not only when it is finished. Treat the
conversation as the place where work is discussed, not where it is stored.

**Observability:** Indirect. Files written and commits made during the session
are visible; whether the right things were captured is not.

---

# Asking well

## BP-06 — Be specific: goal, constraints, audience

A vague prompt does not produce a vague answer — it produces a confident answer
to a question you did not quite ask. Every gap left open is filled with an
assumption, and the assumptions are invisible until the output is wrong.

**Doing it well:** say what the thing is for, what it must not do, who reads it,
and what "done" means. Constraints are more useful than adjectives: "fits in one
screen" beats "concise".

**Observability:** Direct.

## BP-07 — Show a concrete example

One sample of the output you want steers faster and more precisely than several
paragraphs describing it, because it resolves a dozen small format questions at
once without either side having to name them.

**Doing it well:** paste an example of the thing — a previous output you liked, a
before-and-after pair, a sample row. Where the output is a change to existing
material, point at the material.

**Observability:** Direct, but frequently not applicable — many tasks give no
natural occasion for an example.

## BP-08 — Spell out the format

Length, structure, prose against bullets, code against explanation: unstated
means guessed. A sentence naming the format costs less than the rewrite that
follows when the guess is wrong.

**Doing it well:** name the shape up front. Where the output feeds something else
— a file, a commit message, another tool — say so, because that usually
determines the format entirely.

**Observability:** Direct.

## BP-09 — Iterate; treat the first answer as a draft

Trying to get everything right in one enormous prompt front-loads all the risk
onto the moment you have the least information. The first response is most useful
as a way of finding out what you actually wanted.

**Doing it well:** ask, read, correct. Expect two or three passes on anything
substantial, and prefer a quick rough answer that can be steered over a long one
that has to be argued with.

**Observability:** Direct.

## BP-10 — Do not inject the answer

Supplying three examples of what you have in mind narrows the search to their
neighbourhood. This is exactly what you want when you know the shape of the
answer — and exactly what you do not want when you are asking because you do not.

**Doing it well:** when you want options you have not thought of, ask open, then
narrow once the range is on the table. When you want conformity to a pattern,
seed it deliberately. The mistake is doing the second while believing you are
doing the first.

**Observability:** Direct.

## BP-11 — Zoom out first, zoom in on request

Starting at full detail spends tokens and reading time on things that may turn
out not to matter. Starting at the shape lets you choose where the detail is
worth having.

Volume is not thoroughness. A long answer transfers the work of finding the point
back to the reader.

**Doing it well:** ask for the structure before the substance — the architecture
before the file list, the approach before the implementation. A rough diagram
often settles in seconds what paragraphs argue about.

**Observability:** Direct.

---

# Delegation and determinism

## BP-12 — Send wide, read-heavy work to a subagent

Reading a dozen files into the main conversation to answer one question leaves
all twelve in context permanently, crowding out the thing you actually care
about. A subagent reads them somewhere else and reports back the conclusion.

The same applies to work that is naturally separate — a review pass, a broad
search, a survey of how something is done across a codebase.

**Doing it well:** delegate when the answer is small but finding it means reading
a lot. Keep it in the main conversation when the material itself is what you need
to work with.

**Observability:** Direct.

## BP-13 — Offload deterministic work to scripts

A fixed procedure described in prose is reconstructed by the model on every run,
slightly differently each time, at the cost of tokens and the risk of variation
where none was wanted. Written once as a script, it runs the same way forever and
can be tested.

**Doing it well:** when you notice the same sequence of steps being re-derived —
a version bump, an index rebuild, a release, a file transformation — write it
down as code and call it. Judgement belongs in the prompt; procedure belongs in a
script.

**Observability:** Indirect. Repeated manual sequences are visible; whether a
script already existed for them needs the filesystem.

## BP-14 — Use reference files so context loads on demand

Skills load in three stages: the description is always in context, the body loads
when the skill fires, and bundled files load only when something needs them.
Detail placed in the body is paid for on every invocation, including the ones
that never touch it.

**Doing it well:** keep the body to what every run needs and move the rest into
reference files, pointing at them clearly enough that they are found when they
are relevant. This is the same principle as BP-02, applied one level down.

**Observability:** Structural.

---

# Trust

## BP-15 — Verify; confident and correct are different things

Fluency is not evidence. A wrong answer arrives in the same assured prose as a
right one, and the cases where it matters most — numbers, edge cases, anything
load-bearing — are exactly the cases where the prose is most reassuring.

**Doing it well:** check the things a mistake would be expensive in. Ask what was
actually verified rather than assuming the claim implies a check, and treat
"I confirmed X" as a claim to test rather than a result.

**Observability:** Indirect. Whether checks were run is visible; whether the right
things were checked is not.

## BP-16 — Read the actual diff

Accepting changes without reading them accumulates drift that is invisible one
change at a time and expensive to unpick later. The diff is the only place where
what was actually done is stated exactly.

**Doing it well:** read what changed before accepting it, in proportion to what a
mistake would cost. Small steps (BP-03) are what make this affordable — the
practice fails mostly because the changes got too big to review.

**Observability:** Indirect.

## BP-17 — Keep a human deciding anything with real consequences

Drafting and suggesting are safe. Deciding is not. Anything touching money, legal
exposure, or an action that cannot be undone needs a person making the call, with
enough information to actually make it rather than to rubber-stamp it.

This is sharpest where the decision is about a person — hiring, credit, access,
eligibility. A design that lets a model decide such a thing without meaningful
human review is a problem to name, not an implementation detail.

**Doing it well:** let the model prepare, compare and recommend; keep the
irreversible step behind a person. Treat "meaningful review" as requiring that
the reviewer could realistically disagree.

**Observability:** Indirect, and frequently not applicable — most sessions
contain no such decision.

## BP-18 — Mind what you share

A prompt leaves your machine. Credentials, personal data, client material and
internal documents do not stop being sensitive because they were pasted into a
tool rather than emailed. Where personal data is involved, putting it in a prompt
is already processing it.

**Doing it well:** check before sending rather than noticing afterwards —
afterwards is too late. Anonymise personal data unless the real values are
genuinely in scope. Reference where a secret lives instead of reproducing its
value.

**Observability:** Direct. Sensitive material in what was sent is detectable;
absence of a problem is not proof of care.

---

# Setup

## BP-19 — Keep rules in separate files

Instructions that apply across projects — how to handle confidential material,
how to write commits, what to do before anything outbound — belong in their own
rule files rather than being restated in each project. Separate files can be
composed, reused and changed in one place.

**Doing it well:** a rule file per concern, named for the concern. Project
instructions then carry only what is specific to that project, which also keeps
BP-02 achievable.

**Observability:** Structural.
