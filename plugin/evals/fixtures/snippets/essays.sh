
# Something else to grade against a rubric, so the "grade the essays" near miss
# has a referent. Without it the prompt is unanswerable and silence proves
# nothing about the description.
mkdir -p essays
cat > essays/rubric.md <<'EOF'
# Essay rubric

A: clear thesis, every paragraph supports it, sources cited.
B: clear thesis, some paragraphs drift.
C: thesis unclear or unsupported.
EOF
printf 'Remote work helps teams because it widens hiring. Studies agree (Smith 2021).\n' > essays/one.md
printf 'Remote work is good and also bad and it depends on lots of things.\n' > essays/two.md
git add -A
GIT_AUTHOR_DATE='2026-09-19T10:30:00' GIT_COMMITTER_DATE='2026-09-19T10:30:00' \
  git commit -qm 'Add two essays to grade'
