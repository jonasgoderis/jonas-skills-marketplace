#!/usr/bin/env bash
# Builds the fixture repo every release-version case runs against: a short
# history with something worth releasing, and a version source to bump.
#
# Run by `claude plugin eval --scaffold` in the case workspace, which is the
# working directory. No network, no GitHub.
set -eu

git init -q -b main .
git config user.email eval@example.invalid
git config user.name  Eval

printf '0.3.0\n' > VERSION
mkdir -p src
printf 'hello\n' > src/app.txt
git add -A
git commit -qm "Initial commit"

git checkout -qb add-greeting
printf 'greeting\n' >> src/app.txt
git add -A
git commit -qm "Add a greeting to the app"
