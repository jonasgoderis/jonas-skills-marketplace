#!/usr/bin/env bash
# The world every release-version trigger case wakes up in.
#
# The eval sandbox starts with an empty working directory, so without a fixture
# a release prompt has no referent and the skill is right not to fire. This
# gives it one: a small project with a version to bump, a finished feature
# branch, and a dependency that a "bump" question could plausibly be about, so
# the negative cases are a fair test rather than a trick.
#
# Run by `claude plugin eval --scaffold` in the case workspace, which is the
# working directory. No network, no GitHub, no remote.
set -eu

git init -q -b main .
git config user.email eval@example.invalid
git config user.name  Eval
git config commit.gpgsign false

cat > README.md <<'EOF'
# greeter

A very small application that says hello.
EOF

printf '0.3.0\n' > VERSION

cat > package.json <<'EOF'
{
  "name": "greeter",
  "version": "0.3.0",
  "dependencies": {
    "lodash": "^4.17.20"
  }
}
EOF

mkdir -p src
printf 'hello\n' > src/app.txt

commit() { # date, message
  git add -A
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -qm "$2"
}

commit '2026-09-14T10:00:00' 'Initial commit'

git checkout -qb add-greeting
printf 'greeting\n' >> src/app.txt
commit '2026-09-17T09:30:00' 'Add a greeting to the app'

printf 'goodbye\n' >> src/app.txt
commit '2026-09-18T16:05:00' 'Add a parting message'
