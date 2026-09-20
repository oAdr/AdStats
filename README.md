# AdStats

AdStats is an owner-operated QQ bot that provides authorized users with read-only Hypixel player statistics by Minecraft username. It runs on a server and returns a generated image reply. It is not a Minecraft client, mod, or gameplay automation tool.

This public repository contains a small reference implementation of the Hypixel request path and a public verification page. The production QQ gateway, administrator controls, allowlists, and server credentials are intentionally excluded.

## Public files

- `adstats_public_bot.py`: a stateless Python reference client. It resolves a Minecraft username, performs one Hypixel player request, and prints a limited summary. It writes no files, databases, caches, or logs.
- `bot-version.json`: machine-readable version and data-handling declaration for the public reference client.
- `index.html`: a browser-readable description for API review.

## Hypixel API use

For each accepted lookup, the reference client sends one read-only request:

```text
GET https://api.hypixel.net/v2/player?uuid=<UUID>
API-Key: <key supplied through the process environment>
```

The response is used only in memory to report the player name, UUID, rank value when present, and whether the BedWars, SkyWars, and Duels statistic sections are available. No Hypixel write endpoint is called. The key is never placed in the URL or printed.

## Privacy and retention

The public reference client has no persistence layer. It does not create or update files, SQLite databases, query logs, result caches, telemetry, or player-history records. HTTP requests use `Cache-Control: no-cache, no-store`. The process exits after printing the summary; data held in memory is discarded by the operating system.

The production AdStats bot applies its own QQ authorization, temporary image cleanup, and query-audit policy on the operator's server. Those operational files are not part of this public repository.

## Security

The reference client reads `HYPIXEL_API_KEY` from the process environment. A key must be supplied by the operator at run time and is never written by the program. Error output contains only fixed categories and never echoes an API key or upstream response body.

## Traffic controls

The production bot has a pending lookup queue capacity of three and serializes renderer execution. It can enforce an administrator-controlled per-user cooldown from 1 to 3600 seconds. The public reference client itself performs one request per invocation and does not retry or cache a response.

## Version

The production package associated with this application is AdStats 1.8.6. The files in this repository are the separately audited public reference version described by `bot-version.json`; they are deliberately free of deployment credentials and persistent storage.
