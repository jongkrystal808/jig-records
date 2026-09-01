# Fixture-M Lite Repository Instructions

These instructions apply to the entire repository. Keep this file concise and durable; put detailed implementation history in `doc/`.

## 1. Project Scope

Fixture-M Lite is a lightweight fixture inventory and production-capacity platform focused on:

- fixture inventory, receipt, return, and stock warnings
- customer-scoped fixture visibility
- fixture, model, and station relationships
- maximum station capacity for a selected `model + station`
- storage-location and optional file-based fixture-image lookup
- search-first production-floor workflows
- role-based access and customer assignment

Do not turn the Lite product into a lifecycle-heavy MES, workflow engine, or broad BI platform. The implemented inventory/configuration report is an operational read model; it does not authorize unrelated analytics expansion.

## 2. Sources of Truth

- Current code, migrations, and tests define implemented behavior.
- `doc/ARCHITECTURE.md` describes the detailed architecture.
- `doc/ARCHITECTURE_LANDING.md` summarizes delivered and deferred scope.
- `doc/frontend-map.md`, `doc/backend-map.md`, and `doc/map.md` are navigation maps.
- `doc/task.md` and `doc/update.md` are progress/history records; do not rewrite old dated entries as if they were current state.

When documentation and code disagree, verify the behavior in code and tests, then update the current-state documentation as part of the same change.

## 3. Architecture Boundaries

Business logic belongs primarily in backend services.

| Layer | Responsibility |
|---|---|
| Frontend | UI rendering, interaction flow, simple client validation |
| Routers | Endpoint wiring, dependency injection, query/body mapping |
| Services | Business rules, permissions, calculations, aggregation, transactions |
| Repositories | Database queries and persistence |
| Schemas | Request/response contracts |
| Models | ORM/database mapping |
| Core | Configuration, authentication, database, logging, migration bootstrap |

Rules:

- Keep routers thin; do not move business orchestration into route handlers.
- Keep database access in repositories rather than page, router, or schema code.
- Do not implement business workflows with stored procedures, triggers, or giant SQL views.
- Complex reporting SQL may live in a dedicated repository when it is explicit, tested, and orchestrated through a service.
- Prefer FK, unique, NOT NULL, and index constraints for database integrity; keep permission branching and calculations out of the database.

## 4. Business Invariants

### Customer scope and permissions

- Authenticated `super_admin`, `admin`, and `user` sessions are limited to customers assigned through `user_customers`.
- `manage` permission does not bypass customer assignment.
- `super_admin` can manage customers and users, but customer-scoped business data remains limited to assigned customer scope.
- `admin` can manage transaction ledgers and fixture data quality only inside assigned customer scope.
- `user` can edit business data only inside assigned customer scope and cannot perform admin-only management.
- `guest` can read all customers but is read-only, cannot use `/master`, and cannot enter production configuration.
- Enforce scope and permission rules in the backend even when the frontend hides an action.

### Inventory

- Transaction items use the unified `identifier` contract.
- Pure numeric identifiers of length 1–4 are normalized according to the shared identifier utilities; other legacy identifier/datecode values remain literal.
- `ownership_type` belongs to transaction items, not fixture master data.
- Stock summary changes must remain consistent with persisted transaction items.
- Stock status is:
  - `out_of_stock` when `stock_qty <= 0`
  - `low_stock` when `0 < stock_qty < min_stock_qty`
  - `normal` otherwise
- Permanent fixture deletion must preserve or delete transaction history only through the explicit admin choice and must retain deleted-fixture snapshots when history is preserved.

### Production capacity

- `fixture_requirements` is scoped by `model_id + station_id + fixture_id`.
- The same station may be shared by multiple models, but requirements remain model-specific.
- Never infer a model from `station_id` alone.
- Capacity queries and calculations must know both `model_id` and `station_id`.
- Authoritative capacity is `MIN(floor(current_stock_qty / required_qty))` across the complete requirement set for that model and station.
- Do not restore the retired `current_open_station_count` API/UI semantics.

### Storage and images

- Authoritative fixture storage fields are `line_storage_location` and `department_storage_location`; either field may be empty.
- `line_storage_location` and `department_storage_location` are also operator-friendly input sources for the normalized storage index. Split half-width or full-width comma-separated values, trim them, de-duplicate them, and auto-register unknown values as customer-scoped `storage_codes`.
- Storage organization uses `storage_containers`, `storage_codes`, and `fixture_placements`; do not reintroduce the removed single `fixtures.storage_location` column or the retired pre-Lite warehouse profile/location schema.
- A fixture placement targets either one storage code or one complete `model_id + station_id` pair. Never resolve a short station code such as `T2` without fixture/model context; ambiguous station codes remain explicit storage codes until the user resolves them.
- Placement quantities may be left pending, but known allocated quantities must not exceed the fixture stock summary. Do not claim a per-location count from presence-only placement data.
- Fixture images are optional files resolved by fixture code from the configured image directory; do not add image database tables without an explicit design change.

## 5. Frontend Direction

- The current application shell is top-nav-first; mobile navigation uses a drawer. Do not describe or rebuild a persistent desktop sidebar unless explicitly requested.
- `/search` is the shared query/report home. Preserve query/report route state and guest read-only behavior.
- Use the existing Vue 3 + TypeScript API clients, composables, utilities, and shared `Ui*` components before adding page-local duplicates.
- Use the application confirmation flow in `frontend/src/confirmState.ts`; do not add native `window.confirm` calls.
- Preserve keyboard access, focus handling, accessible names, mobile layouts, loading states, and empty states.
- Use green/orange/red only for semantic normal/warning/danger status; keep the application action palette blue/neutral.
- Favor clear production-floor readability over cramped ERP-style density.

## 6. Migrations and Runtime Safety

- Alembic is the authoritative schema-evolution path.
- Add a new revision for schema changes; do not add silent startup schema patches.
- Determine the current migration head from the repository before creating a revision instead of copying a hard-coded head from documentation.
- Preserve the fail-loud runtime migration gate and offline compatibility workflow unless the task explicitly changes that design.
- Treat `backend/app/core/schema_patch.py` as a historical migration dependency, not a general startup fallback.
- Validate migrations against SQLite test coverage and, when deployment work is in scope, a staging copy of MySQL.

## 7. Verification Commands

Run checks proportional to the change. Use the project virtual environment on Windows.

Backend full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Backend targeted examples:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_configuration_report.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_migrations.py -q
```

Frontend tests and production build:

```powershell
Set-Location frontend
npm test
npm run build
```

Do not claim a check passed unless it was run successfully. If a full suite is impractical, run the closest targeted checks and state what was not run.

## 8. Documentation Synchronization

Update documentation in the same change when any of these change:

- routes, API contracts, permissions, or customer scope
- database fields, migrations, or storage rules
- page ownership, shared components, or important frontend flows
- deployment commands, environment variables, or verification baselines
- delivered/deferred product scope

Keep current-state claims separate from dated historical records. Avoid machine-local absolute links in repository documentation; use repository-relative links.

## 9. Change Safety and Completion

- Preserve unrelated user changes in a dirty worktree.
- Do not reset, delete, or overwrite unrelated files to make checks pass.
- Do not edit generated build output, databases, uploads, audit logs, presentation artifacts, or temporary inspection files unless the task explicitly requires it.
- Keep changes scoped; avoid opportunistic refactors unrelated to the request.
- A change is complete only when implementation, proportional verification, and relevant documentation agree.
