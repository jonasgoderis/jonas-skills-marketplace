#!/usr/bin/env bash
# Runs the release-version eval suite.
#
#   eval.sh              every case
#   eval.sh trigger      the eight trigger cases only (cheap, ~$2)
#   eval.sh behaviour    the two behavioural cases only
#   eval.sh <name>       one case by name
#
# Anything after the selector is passed through to `claude plugin eval`, so
# `eval.sh trigger --runs 1` works for a quick look.
#
# This gates nothing. It costs real money and its judge grader is stochastic,
# so it is run on purpose — after changing a skill's description or its
# procedure — not on every commit.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Pinned on purpose. Unpinned, a model release moves the scores and a
# regression is indistinguishable from a model change. Change these
# deliberately and re-record the baseline in docs/plans/ when you do.
MODEL="${EVAL_MODEL:-claude-sonnet-5}"
JUDGE_MODEL="${EVAL_JUDGE_MODEL:-claude-haiku-4-5-20251001}"

# Below 1.0 on purpose: cut-a-release carries an llm grader that lands between
# 0.8 and 0.87 with every deterministic grader green. Gating at 1.0 would make
# a healthy suite look broken. See the Phase 3 notes in
# docs/plans/2026-09-18-release-version-eval-plan.md.
THRESHOLD="${EVAL_THRESHOLD:-0.8}"
MAX_COST="${EVAL_MAX_COST:-8}"

sel="${1:-}"; [ $# -gt 0 ] && shift
case "$sel" in
  ""|all)              filter=() ;;
  trigger|behaviour)   filter=(--tag "$sel") ;;
  *)                   filter=(--case "$sel") ;;
esac

# --no-publish is not optional. The HTML report would otherwise be uploaded to
# claude.ai carrying repo paths, commit messages and diff text.
#
# --scaffold and --allow-tools run author-supplied bash as you. That is what
# builds each case's fixture repo; read plugin/evals/fixtures/ before trusting
# a suite you did not write.
#
# --ablation none: the no-plugin baseline arm cannot fire the skill, so every
# positive fails it by construction. One arm, half the cost, nothing lost.
set -x
exec claude plugin eval plugin \
  "${filter[@]}" \
  --ablation none \
  --model "$MODEL" \
  --judge-model "$JUDGE_MODEL" \
  --threshold "$THRESHOLD" \
  --max-cost-usd "$MAX_COST" \
  --concurrency 4 \
  --scaffold \
  --allow-tools Bash Write Edit \
  --trust-plugin \
  --no-publish \
  "$@"
