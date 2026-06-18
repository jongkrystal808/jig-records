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
- transaction CSV export / import / template flow is implemented
- frontend batch paste import modal is implemented
- on-the-fly fixture creation from inventory batch flow is implemented

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
- fixture image preview and transaction context are implemented
- audit log API is implemented
- recent audit summary is surfaced in the app shell

### Migration / startup compatibility

- Alembic is the primary schema evolution path
- startup migration preflight is implemented
- legacy revision normalization is implemented
- runtime schema patch remains only as compatibility fallback
- current migration chain extends through `0009_remove_owners_and_scope_fixture_code`

## Current Finalized Decisions

### Data model

- `fixtures.code` is unique within `(customer_id, code)`, not globally unique
- fixture storage uses only `fixtures.storage_location`
- `ownership_type` belongs to material transaction items
- transaction identifier model is unified as `identifier`
- fixture responsibility uses `fixtures.responsible_user_id`
- `fixture_requirements` scope is `model_id + station_id + fixture_id`

### UI shell

- app shell is sidebar-first, not top-nav-first
- login and guest entry live in `App.vue` before route content
- `/inventory` and `/inventory/overview` are two entry routes into the same page component
- today receipt / return / low-stock summary live in the sidebar

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
2. Run frontend build
3. Apply migrations against a staging copy of the production database
4. Verify at least one account per role: `admin` / `user` / `guest`
5. Verify customer-scoped users cannot access unauthorized customer data
6. Verify fixture image directory is mounted and readable in deployment

## Quick Start

1. `docker compose up --build -d`
2. Open `http://localhost:8080` for the web app
3. Open `http://localhost:8010/docs` for direct API docs
