# Clean Architecture API — Go & Python FastAPI

A faithful Python (FastAPI) rewrite of the [Golang Clean Architecture](https://github.com/max38/golang-clean-code-architecture) template, implementing the same four-layer clean architecture. Includes a React (Vite + TypeScript) frontend as a bonus.

> **Original Go implementation** by [@max38](https://github.com/max38) is preserved unchanged in `src/`. The Python implementation lives in `python-app/` and the React frontend in `frontend/`.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Go vs Python Comparison](#go-vs-python-comparison)
- [Project Structure](#project-structure)
- [Quick Start — Docker (Recommended)](#quick-start--docker-recommended)
- [Manual Setup — Local Development](#manual-setup--local-development)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Authentication Flow](#authentication-flow)
- [Running Tests](#running-tests)
- [Adding New Models](#adding-new-models)

---

## Architecture Overview

Both implementations follow Uncle Bob's **Clean Architecture** with four distinct layers that depend only inward:

```
┌─────────────────────────────────────────────┐
│           Interface Layer                    │
│  HTTP Handlers  │  Repository Impls          │
├─────────────────────────────────────────────┤
│           Use Case Layer                     │
│  UserUsecase  │  CrudUsecase                 │
├─────────────────────────────────────────────┤
│           Domain Layer                       │
│  Entities  │  Models  │  Repository ABCs     │
├─────────────────────────────────────────────┤
│           Infrastructure Layer               │
│  FastAPI / GoFiber  │  PostgreSQL  │  MongoDB │
└─────────────────────────────────────────────┘
```

**The rule**: inner layers never know about outer layers. Use cases don't import handlers. Domain entities don't import SQLAlchemy.

---

## Go vs Python Comparison

| Concern | Go Implementation | Python Implementation |
|---|---|---|
| **Framework** | GoFiber v2 | FastAPI 0.111 + Uvicorn |
| **ORM** | GORM v1.25 (pgx v5) | SQLAlchemy 2.0 async (asyncpg) |
| **MongoDB** | mongo-driver v1.12 | Motor 3.4 (async) |
| **JWT** | golang-jwt/jwt v5 (HS256) | python-jose[cryptography] (HS256) |
| **Password hashing** | bcrypt cost 10 | bcrypt (direct, cost 10) |
| **Config** | koanf v2 (dotenv + env overlay) | pydantic-settings (dotenv + env overlay) |
| **API Docs** | swaggo (manual annotations) | FastAPI auto-generated OpenAPI |
| **Migrations** | GORM AutoMigrate | Alembic (explicit, versioned) |
| **Dependency Injection** | Manual constructor injection | FastAPI `Depends()` |
| **Async** | Goroutines | `async`/`await` throughout |
| **Tests** | — | pytest + pytest-asyncio (84% coverage) |
| **Config loading** | `.env.dev` → OS env vars (`GOAPP_` prefix) | `.env` → OS env vars (no prefix) |
| **Profile endpoint** | `POST /users/profile` (bug in Go) | `GET /users/profile` (fixed) |
| **Refresh token bug** | Reads `JWT_ACCESS_EXPIRES` for refresh (Go bug) | Correctly reads `JWT_REFRESH_EXPIRES` (fixed) |

---

## Project Structure

```
golang-clean-code-architecture/
│
├── src/                            ← Original Go implementation (untouched)
│   ├── config/                     ← koanf config loader + model registry
│   ├── domain/                     ← Entities, ORM models, repo interfaces
│   ├── infrastructure/             ← GoFiber server, GORM, Motor connectors
│   ├── interface/                  ← HTTP handlers, repository implementations
│   ├── shared/                     ← JWT, bcrypt, slug converter, Avro schema
│   └── usecases/                   ← UserUsecase, CrudUsecase
│
├── python-app/                     ← Python FastAPI implementation
│   ├── src/
│   │   ├── config/                 ← pydantic-settings (Settings, get_settings)
│   │   ├── domain/
│   │   │   ├── entities/           ← Pydantic schemas (UserEntity, request/response)
│   │   │   ├── models/             ← SQLAlchemy ORM models (UserModel, etc.)
│   │   │   └── repositories/       ← ABC interfaces (IUserRepository, ICRUDRepository)
│   │   ├── infrastructure/
│   │   │   ├── database/           ← Async DB connectors (SQLAlchemy, Motor)
│   │   │   └── server/             ← FastAPI app, middlewares, DI dependencies
│   │   ├── interface/
│   │   │   ├── handlers/           ← HTTP route handlers (user, crud, monitor)
│   │   │   └── repositories/       ← Repo implementations (Postgres, MongoDB, factory)
│   │   ├── shared/
│   │   │   ├── authentication/     ← JWT utils (create, parse, repeat)
│   │   │   └── crud/               ← Constants, slug converter, Avro schema generator
│   │   └── usecases/               ← UserUsecase, CrudUsecase
│   ├── alembic/                    ← Database migration files
│   ├── tests/                      ← pytest suite (184 tests, 84% coverage)
│   ├── main.py                     ← App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh               ← Runs migrations then starts server
│
├── frontend/                       ← React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── api.ts                  ← API client (all endpoints)
│   │   ├── pages/                  ← AuthPage (register/login), Dashboard
│   │   └── components/             ← CRUDViewer (data explorer + schema)
│   ├── Dockerfile
│   └── vite.config.ts
│
├── docker-compose.yml              ← All services: db, mongodb, python-app, frontend
├── env.template                    ← Go environment variables template
└── README.md                       ← This file
```

---

## Quick Start — Docker (Recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
# 1. Clone the repo
git clone https://github.com/Manopphysics/golang-clean-code-architecture.git
cd golang-clean-code-architecture

# 2. Create the Python app environment file
cp python-app/.env.example python-app/.env

# 3. Start everything
docker-compose up --build
```

That's it. On first boot:
- PostgreSQL and MongoDB start and become healthy
- The Python app waits for both DBs, then runs Alembic migrations automatically
- The React frontend is built and served

| Service | URL |
|---|---|
| React Frontend | http://localhost:3000 |
| Python API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| MongoDB | localhost:27017 |
> **Note:** The original Go API is NOT started by docker-compose. To run it, follow the Go setup below.

---

## Manual Setup — Local Development

Use this when you're actively editing code and want hot-reload.

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop (for the databases)

### Step 1 — Start the databases

```bash
docker-compose up db mongodb
```

Wait for both to show `healthy` in the logs.

### Step 2 — Python API

```bash
cd python-app

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create the .env file
cp .env.example .env
# Edit .env if needed — defaults match docker-compose

# Run database migrations
alembic upgrade head

# Start the API with hot-reload
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

API available at http://localhost:8000 · Docs at http://localhost:8000/docs

### Step 3 — React Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend available at http://localhost:3000 (or whichever port Vite picks).

### Go API (original)

```bash
# Copy env template
cp env.template .env.dev

# Run migrations
go run src/infrastructure/database/postgres/migration/main.go

# Start the server
go run src/infrastructure/gofiber/main.go
```

Go API available at http://localhost:3000 · Swagger at http://localhost:3000/swagger/

---

## Environment Variables

Copy `python-app/.env.example` to `python-app/.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `APP_HOST` | `127.0.0.1` | Bind host |
| `APP_PORT` | `8000` | Bind port |
| `APP_NAME` | `Python Clean Architecture API` | App name (used as JWT issuer) |
| `APP_VERSION` | `1.0.0` | App version |
| `POSTGRES_DB_NAME` | `postgres` | PostgreSQL database name |
| `POSTGRES_DB_USER` | `postgres` | PostgreSQL user |
| `POSTGRES_DB_PASSWORD` | `golang-first-api` | PostgreSQL password |
| `POSTGRES_DB_HOST` | `localhost` / `db` | `localhost` for local dev, `db` for Docker |
| `POSTGRES_DB_PORT` | `5432` | PostgreSQL port |
| `MONGODB_ATLAS_URI` | `mongodb://root:...@127.0.0.1:27017/...` | Full MongoDB connection URI |
| `MONGODB_DB_NAME` | `golang_cleancode_example` | MongoDB database name |
| `SECRET_KEY` | `1234567890` | JWT signing secret — **change in production** |
| `JWT_ACCESS_EXPIRES` | `86400` | Access token lifetime in seconds (1 day) |
| `JWT_REFRESH_EXPIRES` | `172800` | Refresh token lifetime in seconds (2 days) |

> **Docker vs Local:** When running inside Docker, set `POSTGRES_DB_HOST=db` and use `mongodb` instead of `127.0.0.1` in the MongoDB URI. The `.env.example` comments explain this.

---

## API Reference

Base URL: `http://localhost:8000`  
All routes are prefixed with `/api/v1`.

Full interactive docs available at **http://localhost:8000/docs**.

### Health Check

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/` | None | Returns app name and version |

**Response 200:**
```json
{ "name": "Python Clean Architecture API", "version": "1.0.0" }
```

---

### User Module — `/api/v1/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/users/register` | None | Register a new user |
| `POST` | `/api/v1/users/login` | None | Login, receive access + refresh tokens |
| `POST` | `/api/v1/users/logout` | None | Invalidate session (delete token from DB) |
| `POST` | `/api/v1/users/refresh-token` | None | Get a new access token using refresh token |
| `GET` | `/api/v1/users/profile` | Bearer JWT | Get current user's profile |

#### POST `/api/v1/users/register`

```json
// Request body
{
  "email": "user@example.com",
  "password": "yourpassword",
  "first_name": "John",
  "last_name": "Doe"
}

// Response 201
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}

// Response 400
{ "trace_id": "users-001", "message": "email pattern is invalid" }
```

#### POST `/api/v1/users/login`

```json
// Request body
{ "email": "user@example.com", "password": "yourpassword" }

// Response 200
{
  "user": { "id": 1, "email": "user@example.com", "first_name": "John", "last_name": "Doe", "created_at": "...", "updated_at": "..." },
  "token": { "access": "<jwt_access_token>", "refresh": "<jwt_refresh_token>" }
}

// Response 400
{ "trace_id": "users-002", "message": "password is invalid" }
```

#### POST `/api/v1/users/logout`

```json
// Request body
{ "refresh_token": "<jwt_refresh_token>" }

// Response 200
null

// Response 400
{ "trace_id": "users-004", "message": "user token not found" }
```

#### POST `/api/v1/users/refresh-token`

```json
// Request body
{ "refresh_token": "<jwt_refresh_token>" }

// Response 200 — same shape as login response, new tokens issued
{
  "user": { ... },
  "token": { "access": "<new_access_token>", "refresh": "<new_refresh_token>" }
}

// Response 400
{ "trace_id": "users-003", "message": "token had expired" }
```

#### GET `/api/v1/users/profile`

```
Authorization: Bearer <access_token>
```

```json
// Response 200
{ "id": 1, "email": "user@example.com", "first_name": "John", "last_name": "Doe", "created_at": "...", "updated_at": "..." }

// Response 401
{ "trace_id": "middleware-002", "message": "missing authorization header" }
```

---

### Generic CRUD Module — `/api/v1/data`

All routes require a valid Bearer JWT. The `{slug}` corresponds to a registered entity model:

| Slug | Model | Datasource |
|---|---|---|
| `users` | `UserModel` | PostgreSQL |
| `user-tokens` | `UserTokenModel` | PostgreSQL |
| `user-permissions` | `UserPermissionModel` | PostgreSQL |

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/data/{slug}/describe` | Returns Avro-like schema for the model |
| `GET` | `/api/v1/data/{slug}/` | Paginated list of all records |
| `GET` | `/api/v1/data/{slug}/{id}` | Single record by ID |

#### GET `/api/v1/data/{slug}/describe`

```json
// Response 200
{
  "type": "record",
  "name": "users",
  "fields": [
    { "name": "id", "type": "int" },
    { "name": "email", "type": "string" },
    { "name": "first_name", "type": "string" },
    { "name": "last_name", "type": "string" },
    { "name": "created_at", "type": "datetime" },
    { "name": "updated_at", "type": "datetime" }
  ]
}
```

#### GET `/api/v1/data/{slug}/?_page=1&_pageSize=10`

```json
// Response 200
{
  "code": 200,
  "data": [ { "id": 1, "email": "...", ... } ],
  "page": 1,
  "page_size": 10,
  "total_page": 1,
  "total_data": 1,
  "message": "success",
  "data_schema": { "type": "record", "name": "users", "fields": [...] }
}
```

#### GET `/api/v1/data/{slug}/{id}`

```json
// Response 200
{
  "code": 200,
  "data": { "id": 1, "email": "...", ... },
  "message": "success",
  "data_schema": { "type": "record", "name": "users", "fields": [...] }
}

// Response 400
{ "trace_id": "error", "message": "record '999' not found" }
```

---

## Database Schema

### PostgreSQL Tables

#### `users`
| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT` | PRIMARY KEY, autoincrement |
| `email` | `VARCHAR` | UNIQUE, NOT NULL, INDEX |
| `first_name` | `VARCHAR` | NOT NULL |
| `last_name` | `VARCHAR` | NOT NULL |
| `password` | `VARCHAR` | NOT NULL (bcrypt hash, never returned in API) |
| `created_at` | `TIMESTAMP WITH TZ` | server default: now() |
| `updated_at` | `TIMESTAMP WITH TZ` | server default: now(), auto-updates |

#### `user_tokens`
| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT` | PRIMARY KEY, autoincrement |
| `user_id` | `BIGINT` | FK → users.id (ON DELETE SET NULL), INDEX |
| `access` | `VARCHAR` | Current access token string |
| `refresh` | `VARCHAR` | Current refresh token string |
| `updated_at` | `TIMESTAMP WITH TZ` | auto-updates |

#### `user_permissions`
| Column | Type | Constraints |
|---|---|---|
| `id` | `BIGINT` | PRIMARY KEY, autoincrement |
| `user_id` | `BIGINT` | FK → users.id (ON DELETE SET NULL), INDEX |
| `permission` | `VARCHAR` | Free-form permission string |
| `updated_at` | `TIMESTAMP WITH TZ` | auto-updates |

---

## Authentication Flow

The API uses **stateful JWT** — tokens are stored in the database and validated on every request.

```
Register ──► POST /users/register ──► User created in DB

Login ──────► POST /users/login
               ├─ Verify bcrypt password
               ├─ Issue access token (HS256, 1 day)
               ├─ Issue refresh token (HS256, 2 days)
               ├─ Upsert token row in user_tokens
               └─ Return { user, token: { access, refresh } }

Protected ──► GET /users/profile
  request      ├─ Extract Bearer token from Authorization header
               ├─ Decode JWT (verify signature + expiry)
               ├─ Look up user_tokens WHERE user_id = ? AND access = ?
               ├─ If not found → 401 (token was revoked by logout)
               └─ Set user in request state → handler returns user

Refresh ─────► POST /users/refresh-token
               ├─ Parse refresh token
               ├─ Validate token exists in DB (exact string match)
               ├─ Issue new access token
               ├─ Re-sign refresh token with ORIGINAL expiry (never extended)
               └─ Upsert new tokens in DB

Logout ──────► POST /users/logout
               ├─ Parse refresh token → get user_id
               ├─ Confirm token exists in DB
               └─ Delete token row (all subsequent requests → 401)
```

**JWT Claims structure:**
```json
{
  "claims": { "id": 1 },
  "iss": "python clean architecture api",
  "sub": "access-token",
  "aud": ["user", "admin"],
  "exp": 1234567890,
  "nbf": 1234567890,
  "iat": 1234567890
}
```

---

## Running Tests

```bash
cd python-app

# Install test dependencies (already in requirements.txt)
pip install -r requirements.txt

# Run all tests with coverage report
pytest

# Run a specific test file
pytest tests/test_jwt.py -v

# Run with coverage but no fail threshold
pytest --no-cov-on-fail

# Show only failed tests
pytest --tb=short -q
```

**Coverage summary (as of PR-10):**

| Module | Coverage |
|---|---|
| `src/usecases/` | 100% |
| `src/interface/handlers/` | 100% |
| `src/domain/` | 100% |
| `src/shared/authentication/jwt.py` | 97% |
| `src/shared/crud/` | 100% |
| **Total** | **84.77%** |

> Repository implementations (`postgres/`, `mongodb/`) require a live database and are tested via integration — they are excluded from unit coverage.

---

## Adding New Models

### Python (FastAPI)

1. **Define the SQLAlchemy model** in `python-app/src/domain/models/`:
   ```python
   class ProductModel(Base):
       __tablename__ = "products"
       id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
       name: Mapped[str] = mapped_column(String, nullable=False)
       # ...

       @staticmethod
       def datasource() -> str:
           return "postgresql"  # or "mongodb"
   ```

2. **Generate and apply a migration:**
   ```bash
   cd python-app
   alembic revision --autogenerate -m "add products table"
   alembic upgrade head
   ```

3. **Register the model** in `python-app/src/interface/repositories/crud_factory.py`:
   ```python
   _REGISTERED_MODELS = [
       UserModel,
       UserTokenModel,
       UserPermissionModel,
       ProductModel,  # ← add here
   ]
   ```

4. The model is now accessible via the generic CRUD API at `/api/v1/data/products/`.

### Go (original)

1. Define the model in `src/domain/models/xxxx.go`
2. Register it in `src/config/crudModels.go`
3. Re-run migrations

---

## Tech Stack Summary

### Python FastAPI Stack
- **FastAPI** 0.111 — async web framework with auto OpenAPI
- **SQLAlchemy** 2.0 — async ORM with `asyncpg` driver
- **Motor** 3.4 — async MongoDB driver
- **Alembic** 1.13 — versioned database migrations
- **python-jose** — JWT (HS256)
- **bcrypt** 4.2 — password hashing (cost 10)
- **pydantic-settings** 2.2 — config from env/dotenv
- **pytest** + **pytest-asyncio** + **httpx** — test suite

### Go Stack (original)
- **GoFiber** v2 — HTTP framework
- **GORM** v1.25 — ORM with pgx v5 driver
- **mongo-driver** v1.12 — MongoDB
- **golang-jwt** v5 — JWT (HS256)
- **koanf** v2 — config
- **swaggo** — Swagger docs

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

Original Go implementation © [@max38](https://github.com/max38).  
Python rewrite and React frontend by this fork.
