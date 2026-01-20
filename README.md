# School Billing API

Dockerized FastAPI application for managing schools, students, invoices, and payments, with a focus on clear domain modeling, efficient queries, and a maintainable service-oriented structure.

## Architecture

This project follows a layered architecture with clear separation of concerns:

### 1. Route Layer (`app/routes/`)

Defines HTTP endpoints and request/response schemas

Performs:

- Request validation
- HTTP-level error handling (404, 400)
- Delegates all business logic to the service layer
- Does not contain database logic

### 2. Service Layer (`app/services/`)

Core application/business logic lives here

Services are:

- Explicit use-case driven (e.g. SchoolStatementService)
- Stateless and testable

Responsibilities:

- Query orchestration
- Aggregations and calculations
- Business rule enforcement (e.g. preventing overpayments)
- Database errors are allowed to propagate to global handlers (logged centrally)

### 3. Persistence Layer (`app/models/`)

- SQLAlchemy 2.0 ORM models
- Soft deletes via deleted_at
- Explicit relationships and indexes designed around real query patterns

### 4. Infrastructure / Cross-cutting Concerns

- Global exception handlers for safe error responses
- Structured logging at service and API boundaries
- Prometheus metrics for basic observability

This structure keeps business logic independent from HTTP and infrastructure, enabling easier testing and future extensibility.

## Stack

- **FastAPI** – API framework
- **PostgreSQL** – Primary database
- **SQLAlchemy 2.0** – ORM
- **Alembic** – Database migrations
- **Docker / Docker Compose** – Local development and deployment
- **Ruff** – Linting & formatting
- **Prometheus** – Metrics

## Database Models

Core entities:

**School**

- Owns students
- Entry point for aggregated account statements

**Student**

- Belongs to a school
- Receives invoices

**Invoice**

- Issued to a student
- Contains totals and status (active, cancelled)
- Used as the accounting unit for statements

**InvoiceItem**

- Line-level invoice breakdown
- Allows future extensibility (fees, discounts, adjustments)

**Payment**

- Applied to an invoice
- Supports partial payments
- Used to compute paid vs pending balances

Design choices:

- Soft deletes (deleted_at) used consistently
- Monetary values stored as Decimal
- Addresses intentionally omitted to keep the domain focused
- Normalized relationships, but optimized queries via indexes and aggregation

## Migrations

Managed with Alembic

- Migrations are automatically applied on startup via Docker

Includes:

- Schema evolution
- Optimized indexes for statement queries

Example startup:

```bash
docker-compose up -d --build
```

## Features

**Authentication & Roles**

- Designed to support school-level and admin access
- Separation of concerns between auth and domain logic

**Pagination**

- Applied to list endpoints
- Prevents unbounded result sets

**Prometheus Metrics**

- Request count & latency
- Ready for dashboards and alerting

## Improvements & Technical Decisions

**Error Handling**

Global exception handlers:

- SQLAlchemy errors
- Unhandled exceptions
- Safe, consistent error responses
- No sensitive details leaked to clients

**Logging**

Structured logs at:

- Service boundaries
- Global exception handlers
- Contextual information (endpoint, operation)

**Database Optimization**

Carefully designed partial indexes:

- Active rows only (deleted_at IS NULL)
- Optimized for statement and aggregation queries
- Avoided over-indexing

**Query Optimization**

- Aggregation queries instead of row iteration
- Grouped payment queries to avoid N+1
- Shared base filters to reduce duplication

**Code Quality**

Ruff used for:

- Linting
- Formatting
- Pre-commit hooks enforce style and consistency
- Modular services to avoid duplication

## Testing

**Unit Tests**

- Focus on service layer
- Test business logic independently from HTTP

**End-to-End (E2E) Tests**

- Cover API routes

Validate:

- Request handling
- Database integration
- Error responses

Run tests:

```bash
docker-compose exec app pytest
```

## Quick Start

```bash
# Start services (migrations run automatically)
docker-compose up -d --build
```

API available at:
- http://localhost:8000

Interactive docs:
- http://localhost:8000/docs