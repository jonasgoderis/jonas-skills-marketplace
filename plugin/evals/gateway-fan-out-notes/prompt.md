---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Bash, Skill, Write, Edit]
---

Draw a draw.io diagram of our API Gateway and save it as docs/gateway.drawio. The gateway routes requests to four services: Users, Orders, Payments and Search. Add a note next to Payments: "PCI scoped". Add a note next to Search: "The index rebuilds every night at 02:00. A rebuild takes about 40 minutes, and search results can be up to a day old."
