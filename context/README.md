# SmartHome Context Loading Prompt

Use this file as the entry point for future SmartHome work. The goal is to preserve project guardrails while keeping token usage low.

## Default Prompt For Future Iterations

Before making changes, read only the minimum context needed:

1. Read `context/progress-tracker.md` first to understand current status, completed work, open questions, and latest verification.
2. Read `context/project-overview.md` for product scope only if the task changes user-facing behavior.
3. Read `context/architecture.md` for system boundaries only if the task touches app structure, persistence, scheduler, or API ownership.
4. Read `context/code-standards.md` before code edits.
5. Read `context/feature-design.md` only when changing API contracts, schemas, feature scope, or validation paths.
6. Read `context/ui-context.md` only for UI work.
7. Read `context/ai-workflow-rules.md` only when workflow/process is unclear.
8. Read `context/features/<feature>.md` only for the current feature or a feature being debugged.
9. Read `context/reviewer-test-scenarios.md` only when adding reviewer-flow tests or validating assignment coverage.

Do not scan every context file by default. State which files were read and why before implementing.

## Active Guardrails

- This is a backend-first FastAPI assignment.
- Swagger UI is the primary reviewer/testing surface.
- Keep APIs home-scoped.
- Treat `Home` as the client/home context for v1.
- Vendor integrations are mocked.
- Keep route handlers thin; put business rules in services.
- Keep models, schemas, routers, services, vendors, and scheduler responsibilities separate.
- Do not add auth, real vendor calls, report persistence, or per-appliance scheduler jobs unless explicitly requested.
- Keep `POST /homes/{home_id}/collect` as a manual Swagger/demo helper.
- Preserve `data/.gitkeep`; do not commit SQLite database files.
- Update only the context file that is directly affected by the change.

## Current Implementation Summary

- Python + FastAPI backend.
- SQLite database at `data/smarthome.db`.
- Idempotent startup seeding.
- Home-scoped appliance management.
- Static vendor capability registry with mocked adapters.
- Home-level manual and scheduled metric collection.
- Historical metrics API.
- Daily and custom report APIs generated from metric history.
- APScheduler startup daily report job and default-home collection interval job.
- Root `README.md` contains reviewer run/test/API flow instructions.

## Validation Baseline

Before claiming completion, run:

```bash
.venv/bin/python -m pytest
```

Expected current baseline:

```text
53 passed, 1 FastAPI/Starlette TestClient deprecation warning
```

If a task changes API behavior, also verify the relevant Swagger/API path manually or through an OpenAPI/test assertion.
