---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*\bparent="1")[^>]*\b(?:source|target)="([^"]+)"[^>]*>(?=[\s\S]*<mxCell\b(?=[^>]*\bid="\1")(?=[^>]*\bvertex="1")(?![^>]*\bparent="1")[^>]*>)|<mxCell\b(?=[^>]*\bvertex="1")(?![^>]*\bparent="1")[^>]*\bid="([^"]+)"[^>]*>[\s\S]*<mxCell\b(?=[^>]*\bedge="1")(?=[^>]*\bparent="1")[^>]*\b(?:source|target)="\2"'
match: not_contains
---
