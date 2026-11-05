---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Bash, Skill, Write, Edit]
---

Draw our Azure setup as a draw.io diagram with Azure icons and save it as docs/azure.drawio. A resource group holds an App Service, an Azure Database for PostgreSQL flexible server and a Key Vault. Users outside the resource group call the App Service. The App Service stores data in the database and reads its secrets from the Key Vault. It also calls an external payment provider outside the group, and the payment provider calls the App Service back with a webhook.
