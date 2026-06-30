# AI Workflow Rules

## Approach

Build SmartHome incrementally using a feature-oriented workflow. Each feature must be designed, implemented, and verified through Swagger UI before starting the next feature. Context files define the product scope, architecture, API/schema design, and current progress. Do not infer new behavior outside these files.

## Feature Sequence

Implement in this order:

1. Project foundation and health check.
2. Startup database setup and idempotent seed data.
3. Appliance management.
4. Vendor registry and metric collection.
5. Historical metrics.
6. Reports.
7. Minimal demo UI.

Use `context/feature-design.md` as the source of truth for feature APIs, schemas, and validation paths.

## Scoping Rules

- Work on one feature unit at a time.
- Prefer small, verifiable increments over large speculative changes.
- Do not combine unrelated system boundaries in one implementation step.
- Keep routes, schemas, services, database models, tests, and docs aligned for the active feature.
- Swagger UI must be usable for the active feature before moving on.

## When to Split Work

Split an implementation step if it combines:

- Database setup and business feature behavior.
- Vendor adapter changes and report aggregation changes.
- UI changes and backend API behavior.
- Multiple unrelated API route groups.
- Behavior not clearly defined in the context files.

If a change cannot be verified end to end quickly through Swagger UI or a focused test, the scope is too broad.

## Handling Missing Requirements

- Do not invent product behavior not defined in the context files.
- If a requirement is ambiguous, resolve it in the relevant context file before implementing.
- If a requirement is missing, add it as an open question in `progress-tracker.md` before continuing.
- Keep demo/test helper behavior clearly labeled.

## API and Schema Rules

- Define or update Pydantic request/response schemas before wiring a new route.
- Keep schemas minimal and specific to the API contract.
- Keep SQLAlchemy models focused on persisted state, not response formatting.
- Return consistent JSON shapes that Swagger can show clearly.
- Keep APIs home-scoped for extensibility.

## Protected Files

Do not modify the following unless explicitly required by the active feature:

- Runtime SQLite files under `data/*.db` and `data/*.sqlite`.
- Third-party library internals.

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- Feature scope or API routes: `context/feature-design.md`
- System architecture or storage decisions: `context/architecture.md`
- Code conventions: `context/code-standards.md`
- Current phase and completed work: `context/progress-tracker.md`
- UI behavior: `context/ui-context.md`

## App Structure Rules

- Keep implementation grouped into logical app subsections: models, schemas, routers, services, vendors, static assets, config, and database helpers.
- New models belong under `app/models/`.
- New schemas belong under `app/schemas/`.
- New API routes belong under `app/routers/`.
- New business logic belongs under `app/services/`.
- Keep package `__init__.py` files as stable export points when useful.

## Before Moving to the Next Feature

1. The active feature works end to end within its defined scope.
2. Swagger UI can exercise the feature APIs.
3. Focused tests or a documented manual verification path pass.
4. No invariant defined in `architecture.md` was violated.
5. `progress-tracker.md` reflects the completed work and next feature.
