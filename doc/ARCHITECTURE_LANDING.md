# Architecture Landing

This file maps repository `AGENTS.md` direction to the current implementation state.

Last synchronized with code and tests: 2026-08-31.

## Current Delivery Status

### Platform path

- Browser -> Nginx -> Vue SPA / FastAPI API deployment path is in place
- `docker-compose.yml` serves web + API + database workflow
- frontend reverse proxy is handled in `frontend/nginx.conf`

### Backend layering

- `routers` handle endpoint wiring and HTTP mapping
- business rules live in `services`
- SQL/data access lives in `repositories`
- ORM mapping is in `models`
- request/response contracts are in `schemas`

### Authentication / permissions

- `POST /api/v2/auth/login` is implemented
- `POST /api/v2/auth/guest` is implemented
- JWT-backed session flow is implemented
- role-based permission checks (`read` / `write` / `manage`) are implemented
- authenticated `admin` and `user` sessions are both limited to customers assigned through `user_customers`
- guest mode is read-only and blocked from `/master`

### Master data

- Customers / fixtures / models / stations are implemented
- customer-to-user assignment is implemented through `assigned_user_ids`
- paged customer / fixture / model / station / user read models are implemented for high-volume Form UI maintenance
- paged user responses include customer authorization summaries; Form user maintenance supports searchable multi-customer assignment and requires at least one selected customer before saving
- fixture responsible-user assignment is implemented through `responsible_user_id`
- fixture / model / station CSV import/export/template flows are implemented
- customer-scoped fixture image upload, batch upload, replacement, and lookup are implemented
- image files use `FIXTURE_IMAGE_DIR/<customer_id>/<fixture_code>.<ext>`; GET applies customer scope and permanent fixture deletion cleans up the scoped file

### Inventory

- Receipt / return APIs are implemented
- stock summary / stock alerts / transaction query are implemented
- unified `identifier` inventory model is implemented
- write/query identifier normalization is centralized in a shared backend utility
- frontend batch parsing also uses a shared `identifier` utility so UI-side write normalization stays aligned
- frontend-visible wording can display that same field as `datecode/編號` without changing the contract
- transaction CSV export / import / template flow is implemented
- transaction report export (`xlsx` / `txt`) and preview flow are implemented
- the configuration report uses a backend read model for filtering, sorting, summary aggregation, pagination, linked options, and full-result CSV/XLSX export
- configuration-report responses include stable `populated_columns`, ownership-source stock totals, optional transaction details, and model/station capacity context
- shared frontend batch paste import flow is implemented
- shared frontend batch import uses a spreadsheet-style entry grid for direct cell editing and multi-row/multi-column paste from Excel or other tables
- on-the-fly fixture creation from inventory batch flow is implemented
- onboarding tutorial mode can exercise the batch flow without writing official transactions

### Fixture storage index

- `/storage` provides customer-scoped fixture location lookup and organization without expanding into a full WMS
- comma-separated `line_storage_location` / `department_storage_location` input automatically registers normalized position codes; both `,` and `，` are accepted
- storage codes may remain ungrouped or be collected under a named storage container such as `機櫃1`
- fixture placements target either a storage code or a complete fixture-bound `model + station`; short station codes are resolved only when the fixture context yields one unique pair
- per-location quantity may remain pending, while known allocations are prevented from exceeding current fixture stock
- guest access is read-only; signed-in write roles remain limited to assigned customers

### Production

- model-station mapping is implemented
- fixture requirement CRUD is implemented
- capacity query is implemented
- model query is implemented
- multi-model shared-station rule is implemented
- production CSV import/export/template flows are implemented
- frontend batch paste import modal is implemented for mapping and requirement
- on-the-fly model / station / fixture creation from production batch flow is implemented
- Form production read models are server-paginated and use lazy remote autocomplete instead of preloading complete fixture / model / station option lists
- Form production paste import has customer-scoped preview endpoints; conflicts are not overwritten until the operator explicitly confirms replacement

### Search / audit

- search workspace is implemented
- fixture / model dual-mode search UI is implemented
- empty Modern fixture search shows a paginated customer-scoped fixture overview with stock, status, storage, and active state
- search workspace now uses paginated global search plus `load more`
- fixture / model context is loaded on demand after result selection
- fixture image preview and transaction context are implemented
- first-login onboarding and replayable guided tour are implemented in the frontend shell
- onboarding is now split into selectable tutorial categories instead of one flat sequence
- versioned release notice modal is implemented in the frontend shell
- audit log API is implemented
- recent audit summary API remains available, but is not currently rendered in the app shell

### Migration / startup compatibility

- Alembic is the primary schema evolution path
- startup migration preflight is implemented
- legacy revision normalization is implemented
- runtime startup now uses a fail-loud migration gate instead of silent compatibility patching
- legacy compat handling is still available through `python -m backend.app.tools.migration_check`
- runtime gate outcomes are emitted as structured log events for operator review
- runtime schema patch remains only as a historical backfill dependency, not a startup fallback
- the runtime compatibility gate remains `0011_search_indexes`; this is a minimum startup gate, not the current schema head
- the current Alembic migration chain extends through `0019_fixture_storage`

## Current Finalized Decisions

### Data model

- `fixtures.code` is unique within `(customer_id, code)`, not globally unique
- fixture storage is split into `fixtures.line_storage_location` and `fixtures.department_storage_location`; the legacy single `storage_location` column was removed by revision `0013`
- `ownership_type` belongs to material transaction items
- transaction identifier model is unified as `identifier`
- fixture responsibility uses `fixtures.responsible_user_id`
- `fixture_requirements` scope is `model_id + station_id + fixture_id`
- fixture requirements can optionally designate concrete in-stock identifiers; designated capacity uses only those identifiers while normal requirements use total fixture stock
- fixture location indexing uses `storage_containers`, `storage_codes`, and `fixture_placements`; the two existing fixture storage text fields remain convenient input sources and are not replaced by a single legacy storage column

### UI shell

- app shell is top-nav-first, not sidebar-first
- `App.vue` switches the authenticated application between route-aware Modern, Form, and Workbench system surfaces; all surfaces retain the same canonical feature routes
- Form UI uses dynamic workspace headings and full-text grouped module navigation; route changes reset to the active module/filter top
- Workbench UI targets PC, notebook, and Tablet with a three-column production-floor flow and two-column Tablet adaptation for receipt, return, fixture lookup, and authoritative model/station bottleneck capacity. Its center panel uses the shared Modern batch grid as one combined receipt/return workspace; recent work is fetched from the item-level backend page contract in 50-row pages, signed-in model shortcuts are persisted cross-device while guest shortcuts stay local, and the bottleneck row is explicit. Receipt/return overview, production settings, master data, Admin ledger, and Admin fixture-quality routes use a matching async-loaded management shell with role-aware navigation, collapsible Tablet filters, and retained applied-filter summaries
- Playwright visual regression projects keep deterministic Workbench receipt baselines at 1024, 1366, and 1920 widths and reject page-level horizontal overflow
- guest defaults to Form UI; admin and user can store a per-account Modern/Form/Workbench login default in browser storage
- unauthenticated navigation is routed to the lightweight `/login` route; `App.vue` renders `AppAuthScreen.vue` there, then login or guest entry redirects to `/search`
- `/inventory` and `/inventory/overview` are two entry routes into the same page component
- today receipt / return / low-stock summary live in the top bar
- top bar exposes global `收/退料` and `收退料資訊匯出` actions
- onboarding flow is orchestrated by `App.vue` and `frontend/src/onboarding.ts`
- onboarding flow selection is rendered by a dedicated picker modal in the frontend shell
- shared `UiModalShell.vue` owns focus trapping, initial/return focus, Escape, nested stacking, and background inert behavior for application, onboarding, release, Production, and Master dialogs
- configuration-report route/filter/export state, Master CRUD/deletion, and inventory batch parse/preview/submit lifecycles are isolated in dedicated composables instead of remaining inline in the large page SFCs
- `InventoryRelationsPage.vue`, `MasterPage.vue`, and `ProductionPage.vue` load their large style blocks from `frontend/src/styles/surfaces/`, preserving the prior global/scoped semantics

### Permission model

- `super_admin`: assigned customers only for business data, write + ledger/quality management + customer/user management
- `admin`: assigned customers only, write + ledger/quality management, no customer/user management
- `user`: assigned customers only, write business data, no manage
- `guest`: all customers, read-only, no `/master`

## Deferred / Not Yet in Scope

- Barcode scanning flow
- QR lookup flow
- Mobile-first handheld workflow
- Complex cross-domain analytics dashboards beyond the implemented configuration report and export center
- Lifecycle-heavy MES features

## Suggested Verification Before Production

1. Run backend tests, especially auth / inventory / production / migration coverage
2. Ensure Python environment has `openpyxl` installed before running inventory export tests
3. Run frontend build
4. Apply migrations against a staging copy of the production database
5. Verify at least one account per role: `super_admin` / `admin` / `user` / `guest`
6. Verify customer-scoped users cannot access unauthorized customer data
7. Verify fixture image directory is mounted and writable in deployment

## Quick Start

1. `docker compose up --build -d`
2. Open `http://localhost:8080` for the web app
3. Open `http://localhost:8010/docs` for direct API docs
