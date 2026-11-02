---
type: regex
target:
  source: file
  path: docs/aws.drawio
pattern: '<mxCell\b(?=[^>]*\bvertex="1")(?=[^>]*style="(?:image;|[^"]*shape=(?:image|mxgraph\.)))(?=[^>]*\bparent="([^"]+)")[^>]*>[\s\S]*<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*\bparent="\1")'
match: not_contains
---

Matches an icon that has an edge with the same parent somewhere after it. The backreference compares the parents, so an icon inside a group container may come before an edge on the page, as the skill allows.
