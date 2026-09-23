
# A release whose only change is internal, in a repo whose docs are all still
# true. The features are merged first, so the branch under release carries one
# test-script hardening and nothing a reader of the README or CLAUDE.md would
# notice. CLAUDE.md names the test script, which makes it the near-miss: the
# file it points at changed, and what it says about it did not.
git checkout -q main
git merge -q --ff-only add-greeting
cat > CLAUDE.md <<'CLAUDE'
# greeter

Run `scripts/test.sh` before pushing. Keep src/app.txt one phrase per line.
CLAUDE
commit '2026-09-18T12:00:00' 'Add agent instructions'
git push -q origin main
git checkout -qb harden-tests

cat > scripts/test.sh <<'TEST'
#!/usr/bin/env bash
set -euo pipefail
echo "  ok    the greeting is present"
grep -q greeting src/app.txt
TEST
commit '2026-09-19T09:00:00' 'Make the test script stop on the first error'
