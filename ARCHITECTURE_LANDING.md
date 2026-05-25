# Architecture Landing (Phase 1)

This file maps `AGENT.md` direction to current implementation status.

## Completed in this phase

- Browser -> Nginx -> Frontend/API deployment path
  - Added `web` service in `docker-compose.yml`
  - Added `frontend/` (Vue3 + TypeScript + Pinia + Vite)
  - Added Nginx reverse proxy config in `frontend/nginx.conf`
- Backend service-layer architecture kept intact
  - `routers` only handle request/response
  - business logic in `services`
  - SQL/data access in `repositories`
- Core API domain coverage expanded
  - Master: customers/fixtures/models/stations/owners
  - Inventory: receipts/returns/stock/alerts/transactions
  - Production: model-stations/fixture-requirements/capacity
  - Warehouse: locations/location-assignments/fixture-images
  - Search: global search
- Search-first frontend workflow
  - dashboard + global search + inventory + master + production + warehouse pages

## Not yet in this phase

- JWT auth module (`/api/v2/auth`)
- file upload flow for fixture images (current API stores paths)
- advanced export/report pages
- barcode/QR/mobile mode

## Quick start

1. `docker compose up --build -d`
2. Open `http://localhost:8080` for web app
3. Open `http://localhost:8010/docs` for direct API docs
