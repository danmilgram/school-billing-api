# School Billing API - Execution Plan

## Step 1: Project Architecture ✅
- [x] Create project directory structure
- [x] Set up basic Python project files (pyproject.toml, .gitignore)
- [x] Create app directory with models, routes, schemas, core subdirectories
- [x] Add requirements.txt with FastAPI, SQLAlchemy, Alembic, PostgreSQL dependencies

## Step 2: FastAPI + Database Setup
- [ ] Configure database connection (SQLAlchemy 2.0)
- [ ] Create database models (School, Student, Invoice, Payment)
- [ ] Set up Alembic migrations
- [ ] Create Docker Compose (PostgreSQL + FastAPI services)
- [ ] Add basic FastAPI app setup

## Step 3: Implement API Endpoints
- [ ] CRUD endpoints for Schools
- [ ] CRUD endpoints for Students
- [ ] CRUD endpoints for Invoices
- [ ] Endpoint: School account statement
- [ ] Endpoint: Student account statement

## Step 4: Authorization
- [ ] Add basic authentication/authorization

## Step 5: Testing
- [ ] Unit tests for models
- [ ] Integration tests for endpoints

## Step 6: Extras
- [ ] Cache (Redis) for read endpoints
- [ ] Pagination
- [ ] Observability (logs, health checks)

## Step 7: Documentation
- [ ] README with setup instructions
- [ ] API documentation (OpenAPI/Swagger)

## Step 8: Code Quality
- [ ] Add ruff to requirements
- [ ] Configure ruff in pyproject.toml
- [ ] Format and lint codebase
