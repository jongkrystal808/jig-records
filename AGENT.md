# AGENT.md

# Fixture-M Lite Agent Guidelines

## 1. Project Positioning

Fixture-M Lite is a lightweight fixture inventory and production-capacity management platform.

The system focuses on:

- Fixture inventory management
- Fixture-to-model relationship
- Fixture demand management
- Maximum production station capacity calculation
- Stock warning and shortage alerts
- Warehouse/storage location visibility
- Fast production floor search experience
- Fixture image management

This system is NOT a lifecycle-heavy MES.

The Lite version intentionally removes:

- Complex lifecycle engine
- Usage/replacement calculation engine
- Heavy Stored Procedure logic
- Complex analytics pipeline
- Heavy Trigger-driven business rules

---

## 2. Core Philosophy

Business logic should primarily exist in the backend service layer.

| Layer | Responsibility |
|---|---|
| Frontend | UI rendering, user interaction, simple client validation |
| Backend | Business logic, calculations, validation, aggregation |
| Database | Persistence, FK constraints, indexes, simple integrity protection |

---

## 3. Architecture Rules

### 3.1 Avoid heavy Stored Procedures

Do not implement complex business logic inside:

- Stored Procedures
- Triggers
- SQL Views

Acceptable database logic:

- FK constraints
- Unique constraints
- NOT NULL
- updated_at trigger
- Basic stock protection

Business logic that belongs in backend services:

- Stock calculation
- Stock warning status
- Maximum station capacity calculation
- Fixture requirement validation
- Search result aggregation
- Image/location handling

---

### 3.2 Keep SQL simple

Preferred:

```sql
SELECT *
FROM fixture_stock_summary
WHERE customer_id = ?;
```

Avoid:

- Nested giant views
- Trigger-driven state machines
- Multi-step SP orchestration
- Hidden database-side business flows

---

### 3.3 Prefer Service Layer

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
| core | config/auth/db |

---

## 4. Frontend Design Direction

Target style:

```text
Industrial dashboard + modern card UI
```

Avoid:

- Overly enterprise-heavy ERP UI
- Complex nested tables
- Tiny dense text layouts

Prefer:

- Large visual hierarchy
- Card-based information
- Status colors
- Production floor readability
- Fast search-first workflow

---

## 5. UI Priority

Important information should stand out in this order:

1. Fixture code
2. Fixture image
3. Current stock
4. Stock warning status
5. Storage location
6. Related models
7. Maximum station capacity

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

## 7. Global Search Rules

Global search is a core feature.

Users should be able to search:

- Fixture code
- Fixture name
- Machine model
- Storage location
- Serial number

Search result cards should display:

- Fixture image
- Stock quantity
- Storage location
- Related models
- Capacity status

---

## 8. Core Business Domains

### 8.1 Master Data

Includes:

- Customers
- Fixtures
- Machine models
- Stations
- Owners

### 8.2 Inventory Management

Includes:

- Receipt
- Return
- Inventory query
- Stock movement history
- Export
- Stock warning

### 8.3 Production Configuration

Includes:

- Model ↔ Station mapping
- Fixture requirements
- Maximum station capacity calculation

### 8.4 Warehouse Management

Includes:

- Storage locations
- Fixture image
- Location assignment
- Quick location lookup

---

## 9. Capacity Calculation Logic

Maximum station capacity is a core feature.

Formula:

```text
max_open_station_count = MIN(current_stock_qty / required_qty)
```

Example:

```text
Station T1_MAC requires:
- L-00062 x1
- L-00475 x1

Inventory:
- L-00062 = 326
- L-00475 = 263

Result:
min(326/1, 263/1) = 263
```

This calculation must be handled by backend services.

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

Each fixture should support:

- Main image
- Thumbnail image
- Optional additional images

Recommended storage:

```text
/uploads/fixtures/
```

---

## 12. Storage Location Design

Recommended location format:

```text
A-01-01
A-01-02
B-02-03
```

| Segment | Meaning |
|---|---|
| A | Area |
| 01 | Rack |
| 01 | Layer |

---

## 13. Performance Strategy

Use summary tables:

```text
fixture_stock_summary
machine_capacity_summary
```

Avoid calculating heavy aggregation directly from transaction tables every request.

Backend should update summaries after inventory transactions.

---

## 14. Development Priorities

Highest priority:

- Stable inventory logic
- Search experience
- Capacity calculation
- Storage location visibility
- Stock warning
- Fixture image support

Lower priority:

- Complex analytics
- Historical deep audit
- Lifecycle analysis
- Advanced workflow engine

---

## 15. Recommended Stack

Frontend:

```text
Vue 3
TypeScript
Vite
Pinia
```

Backend:

```text
FastAPI
SQLAlchemy
Pydantic
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
Fixture Warehouse + Production Capacity Platform
```

Focus on:

- Speed
- Clarity
- Production usability
- Search efficiency
- Visual warehouse management

