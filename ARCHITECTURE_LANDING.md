# Architecture Landing

This file maps `AGENT.md` direction to the current implementation state.

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
- customer-scoped access control is implemented for non-admin users
- guest mode is read-only and blocked from `/master`

### Master data

- Customers / fixtures / models / stations are implemented
- customer-to-user assignment is implemented through `assigned_user_ids`
- fixture responsible-user assignment is implemented through `responsible_user_id`
- fixture / model / station CSV import/export/template flows are implemented
- fixture image lookup by fixture code is implemented

### Inventory

- Receipt / return APIs are implemented
- stock summary / stock alerts / transaction query are implemented
- unified `identifier` inventory model is implemented
- write/query identifier normalization is centralized in a shared backend utility
- frontend batch parsing also uses a shared `identifier` utility so UI-side write normalization stays aligned
- frontend-visible wording can display that same field as `datecode/編號` without changing the contract
- transaction CSV export / import / template flow is implemented
- transaction report export (`xlsx` / `txt`) and preview flow are implemented
- shared frontend batch paste import flow is implemented
- shared frontend batch paste import flow supports literal `Tab` insertion in the textarea for manual spreadsheet-style entry
- on-the-fly fixture creation from inventory batch flow is implemented
- onboarding tutorial mode can exercise the batch flow without writing official transactions

### Production

- model-station mapping is implemented
- fixture requirement CRUD is implemented
- capacity query is implemented
- model query is implemented
- multi-model shared-station rule is implemented
- production CSV import/export/template flows are implemented
- frontend batch paste import modal is implemented for mapping and requirement
- on-the-fly model / station / fixture creation from production batch flow is implemented

### Search / audit

- search workspace is implemented
- fixture / model dual-mode search UI is implemented
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
- current migration chain extends through `0011_search_indexes`

## Current Finalized Decisions

### Data model

- `fixtures.code` is unique within `(customer_id, code)`, not globally unique
- fixture storage uses only `fixtures.storage_location`
- `ownership_type` belongs to material transaction items
- transaction identifier model is unified as `identifier`
- fixture responsibility uses `fixtures.responsible_user_id`
- `fixture_requirements` scope is `model_id + station_id + fixture_id`

### UI shell

- app shell is top-nav-first, not sidebar-first
- login and guest entry live in `App.vue` before route content
- `/inventory` and `/inventory/overview` are two entry routes into the same page component
- today receipt / return / low-stock summary live in the top bar
- top bar exposes global `收/退料` and `收退料資訊匯出` actions
- onboarding flow is orchestrated by `App.vue` and `frontend/src/onboarding.ts`
- onboarding flow selection is rendered by a dedicated picker modal in the frontend shell

### Permission model

- `admin`: all customers, write + manage
- `user`: assigned customers only, write business data, no manage
- `guest`: all customers, read-only, no `/master`

## Deferred / Not Yet in Scope

- Dedicated fixture image upload UI/API flow
- Barcode scanning flow
- QR lookup flow
- Mobile-first handheld workflow
- Advanced reporting/export center
- Complex analytics dashboards
- Lifecycle-heavy MES features

## Suggested Verification Before Production

1. Run backend tests, especially auth / inventory / production / migration coverage
2. Ensure Python environment has `openpyxl` installed before running inventory export tests
3. Run frontend build
4. Apply migrations against a staging copy of the production database
5. Verify at least one account per role: `admin` / `user` / `guest`
6. Verify customer-scoped users cannot access unauthorized customer data
7. Verify fixture image directory is mounted and readable in deployment

## Quick Start

1. `docker compose up --build -d`
2. Open `http://localhost:8080` for the web app
3. Open `http://localhost:8010/docs` for direct API docs
