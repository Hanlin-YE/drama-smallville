# Project Agent Instructions

This project uses a project-local PlanDB task graph for Codex coordination.

## Required First Step

When starting work in this project, first inspect PlanDB status from the project root:

```bash
./tools/plandb status --detail
```

If the user asks for project work that is more than a one-off question or trivial edit, claim a ready task before doing the work:

```bash
PLANDB_AGENT=codex-main ./tools/plandb go
```

Use a more specific agent name when appropriate:

```bash
PLANDB_AGENT=codex-research ./tools/plandb go
PLANDB_AGENT=codex-builder ./tools/plandb go
PLANDB_AGENT=codex-reviewer ./tools/plandb go
PLANDB_AGENT=codex-debugger ./tools/plandb go
```

Only work on the task you claimed.

## Shared Project Memory

Write durable information to PlanDB context:

```bash
./tools/plandb context "Decision or discovery." --kind decision
./tools/plandb context "Important constraint." --kind constraint
./tools/plandb context "Unresolved blocker." --kind blocker
./tools/plandb context "Reusable pattern." --kind pattern
```

Use these kinds by default:

- `decision`
- `constraint`
- `blocker`
- `discovery`
- `risk`
- `pattern`
- `handoff`

## Completing Work

Complete claimed tasks with a structured result:

```bash
PLANDB_AGENT=codex-main ./tools/plandb done --result '{"summary":"...", "verification":"...", "risks":[]}'
```

If verification was not run, say so in the result:

```bash
PLANDB_AGENT=codex-main ./tools/plandb done --result '{"summary":"...", "verification":"not run", "risks":["..."]}'
```

## Priority Inspection

Use these commands when deciding what to do next:

```bash
./tools/plandb list --status ready
./tools/plandb critical-path
./tools/plandb bottlenecks
./tools/plandb search "keyword"
```

PlanDB search is keyword/BM25 search, not semantic search. Use concrete terms.

## Trial Boundaries

- Use only `./tools/plandb`.
- Use only this project's `.plandb.db`.
- Do not run the official PlanDB install script.
- Do not modify `~/.codex`.
- Do not enable PlanDB MCP or HTTP server.
- Do not commit `.plandb.db` or `.plandb.db-*`.

Detailed protocol: `docs/plandb-codex-protocol.md`.
