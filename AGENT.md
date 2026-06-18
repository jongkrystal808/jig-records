# AGENT.md

# Fixture-M Lite Agent Guidelines

## 1. Project Positioning

Fixture-M Lite is a lightweight fixture inventory and production-capacity management platform.

The system focuses on:

- Fixture inventory management
- Customer-scoped fixture visibility
- Fixture-to-model and fixture-to-station relationship management
- Maximum station capacity calculation for a selected `model + station`
- Stock warning and shortage alerts
- Storage location visibility
- Search-first production floor workflow
- Optional file-based fixture image preview
- Role-based access and customer assignment

This system is NOT a lifecycle-heavy MES.

The Lite version intentionally avoids:

- Complex lifecycle engine
- Usage/replacement prediction engine
- Heavy stored-procedure business logic
- Trigger-driven workflow orchestration
- Large reporting/analytics subsystem

---

## 2. Core Philosophy

Business logic should primarily live in the backend service layer.

| Layer | Responsibility |
|---|---|
| Frontend | UI rendering, interaction flow, simple client validation |
| Backend | Business logic, permission checks, calculations, aggregation |
| Database | Persistence, FK constraints, indexes, simple integrity protection |

---

## 3. Architecture Rules

### 3.1 Prefer backend services over database logic

Do not implement complex business rules inside:

- Stored Procedures
- Triggers
- Giant SQL Views

Acceptable database logic:

- FK constraints
- Unique constraints
- NOT NULL
- Basic stock integrity protection
- Simple timestamp maintenance

Business logic that belongs in backend services:

- Stock calculation
- Stock warning status
- Maximum station capacity calculation
- Fixture requirement validation
- Search result aggregation
- Customer access scope validation
- Role-based permission enforcement
- File-based fixture image lookup

---

### 3.2 Keep SQL simple and explicit

Preferred:

```sql
SELECT *
FROM fixture_stock_summary
WHERE customer_id = ?;
```

Avoid:

- Deep nested views
- Hidden trigger-driven state machines
- Multi-step SP orchestration
- Database-side permission branching

---

### 3.3 Prefer layered backend structure

Recommended backend structure:

```text
backend/
├─ app/
│  ├─ routers/
│  ├─ services/
│  ├─ repositories/
│  ├─ schemas/
│  ├─ models/
│  ├─ utils/
│  └─ core/
```

| Folder | Responsibility |
|---|---|
| routers | API endpoints only |
| services | Business logic |
| repositories | Database access |
| schemas | Request/response models |
| models | ORM/database models |
| core | config/auth/db/migration bootstrap |

---

## 4. Frontend Design Direction

Target style:

```text
Industrial dashboard + modern card UI
```

Avoid:

- ERP-style cramped dense screens
- Deep nested controls
- Weak visual hierarchy

Prefer:

- Strong summary row
- Search-first workflow
- Card-based sections
- Clear status color language
- Production-floor readability
- Sidebar-centered navigation and session context

---

## 5. UI Priority

Important information should stand out in this order:

1. Current customer / current page intent
2. Fixture code or model code
3. Current stock / capacity result
4. Stock or capacity status
5. Storage location / station context
6. Related models / stations / requirements
7. Transaction and audit context

---

## 6. Status Colors

| Status | Color |
|---|---|
| Normal | Green |
| Low stock | Orange |
| Out of stock | Red |
| Information | Blue |
| Disabled/Inactive | Gray |

---

## 7. Search Rules

Search is a core feature.

Users should be able to search:

- Fixture code
- Fixture name
- Machine model
- Station
- Storage location
- Identifier

Search result cards should display:

- Fixture image
- Stock quantity
- Storage location
- Related models
- Capacity-related context

Search behavior should follow these rules:

- Fixture-side related models come from `fixture_requirements.model_id`
- Do not infer model from station alone
- Fixture detail should show `model + station + required_qty`

---

## 8. Core Business Domains

### 8.1 Master Data

Includes:

- Customers
- Fixtures
- Machine models
- Stations
- Customer-to-user assignment
- Fixture responsible-user assignment

### 8.2 Inventory Management

Includes:

- Receipt
- Return
- Inventory query
- Stock movement history
- CSV export/import
- Batch paste import
- Stock warning

Rules:

- Transaction item uses unified `identifier`
- `ownership_type` belongs to transaction items, not fixture master

### 8.3 Production Configuration

Includes:

- Model ↔ Station mapping
- Fixture requirements
- Maximum station capacity calculation
- Model query

Rules:

- `fixture_requirements` scope is `model_id + station_id + fixture_id`
- Same station may be shared by multiple models
- Capacity query must always know both `model_id` and `station_id`

### 8.4 Access Control

Includes:

- Login
- Guest entry
- Role-based permission checks
- Customer scope filtering

Rules:

- `admin`: all customers, can manage everything
- `user`: assigned customers only, can edit business data
- `guest`: all customers, read-only, no `/master`

---

## 9. Capacity Calculation Logic

Maximum station capacity is a core feature.

Formula:

```text
max_open_station_count = MIN(floor(current_stock_qty / required_qty))
```

Example:

```text
Model T1_MAC at station ST-01 requires:
- L-00062 x1
- L-00475 x1

Inventory:
- L-00062 = 326
- L-00475 = 263

Result:
min(326/1, 263/1) = 263
```

This calculation must be handled by backend services.

Do not:

- infer requirement by `station_id` alone
- calculate cross-station shared consumption in a single-station query
- expose old `current_open_station_count` UI semantics

---

## 10. Stock Warning Rules

Each fixture can define:

```text
min_stock_qty
```

Status rules:

```python
if stock_qty <= 0:
    status = "out_of_stock"
elif stock_qty < min_stock_qty:
    status = "low_stock"
else:
    status = "normal"
```

---

## 11. Image Management

Each fixture may support:

- Optional preview image resolved by fixture code

Recommended storage:

```text
uploads/fixtures/
```

Images are file-based, not stored in dedicated image tables.

---

## 12. Storage Location Design

Authoritative storage field:

```text
fixtures.storage_location
```

Recommended location format:

```text
A-01-01
A-01-02
B-02-03
```

Warehouse profile / assignment tables are intentionally removed in the current design.

---

## 13. Performance Strategy

Use summary-style tables where they simplify frequent reads:

```text
fixture_stock_summary
machine_capacity_summary
```

Notes:

- `fixture_stock_summary` is part of the main read path
- `machine_capacity_summary` is optional/cache-like; runtime production calculation remains authoritative

Avoid recalculating expensive aggregates directly from raw transaction tables on every screen if a maintained summary already exists.

---

## 14. Development Priorities

Highest priority:

- Stable inventory logic
- Correct customer scope enforcement
- Search workflow
- Capacity calculation correctness
- Storage location visibility
- Stock warning
- Fixture image support
- Migration stability

Lower priority:

- Complex analytics
- Deep historical reporting
- Lifecycle analysis
- Workflow engine

---

## 15. Recommended Stack

Frontend:

```text
Vue 3
TypeScript
Vite
Reactive app state + composables
```

Backend:

```text
FastAPI
SQLAlchemy
Pydantic
JWT
```

Database:

```text
MySQL 8
Alembic
```

---

## 16. Final Direction

Fixture-M Lite should evolve toward:

```text
Fixture Inventory + Production Capacity Platform
```

Focus on:

- Speed
- Clarity
- Production usability
- Search efficiency
- Clear location lookup
- Predictable permission boundaries
