# Architecture Documentation

## Clean Architecture Principles

This project implements [Uncle Bob's Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html). The core rule is the **Dependency Rule**: source code dependencies must point only inward — from outer layers to inner layers, never the reverse.

```
        ┌───────────────────────────────────────────┐
        │  Infrastructure (outermost)                │
        │  FastAPI / GoFiber / SQLAlchemy / Motor    │
        │  ┌─────────────────────────────────────┐  │
        │  │  Interface                           │  │
        │  │  HTTP Handlers / Repository Impls    │  │
        │  │  ┌───────────────────────────────┐  │  │
        │  │  │  Use Cases                    │  │  │
        │  │  │  Business Logic               │  │  │
        │  │  │  ┌───────────────────────┐   │  │  │
        │  │  │  │  Domain (innermost)   │   │  │  │
        │  │  │  │  Entities  Models     │   │  │  │
        │  │  │  │  Repo Interfaces      │   │  │  │
        │  │  │  └───────────────────────┘   │  │  │
        │  │  └───────────────────────────────┘  │  │
        │  └─────────────────────────────────────┘  │
        └───────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. Domain Layer (innermost)

**No external dependencies.** Pure Python / Go data structures.

| Component | Go | Python |
|---|---|---|
| Entities | `UserEntity`, `UserTokenEntity` | Pydantic `BaseModel` subclasses |
| ORM Models | `UserModel` (GORM struct) | `UserModel` (SQLAlchemy `DeclarativeBase`) |
| Repository interfaces | `IUserRepository`, `ICRUDRepository` (Go interfaces) | Python ABCs with `@abstractmethod` |

The domain layer defines **what** the app works with, not **how** it stores or retrieves data.

Key Python files:
- `src/domain/entities/user.py` — `UserEntity`, all request/response schemas
- `src/domain/entities/crud.py` — `DataResponse`, `DataListResponse`
- `src/domain/models/user.py` — SQLAlchemy models (`UserModel`, `UserTokenModel`, `UserPermissionModel`)
- `src/domain/repositories/user.py` — `IUserRepository` ABC (9 methods)
- `src/domain/repositories/crud.py` — `ICRUDRepository` ABC (7 methods)

### 2. Use Case Layer

**Depends on: Domain only.** Zero knowledge of HTTP, databases, or frameworks.

Each use case class receives its repository via **constructor injection** (Go) or **`Depends()`** (Python/FastAPI).

| Use Case | Responsibility |
|---|---|
| `UserUsecase` | Register, login, logout, refresh token, authentication, profile |
| `CrudUsecase` | Retrieve one, retrieve list, describe schema |

`UserUsecase.user_login()` flow:
```
1. repo.get_user_by_email(email)        ← domain boundary
2. verify_password(plain, hashed)       ← pure function
3. create_access_token(user_id)         ← pure function
4. create_refresh_token(user_id)        ← pure function
5. repo.upsert_oauth(response)          ← domain boundary
6. return UserLoginResponse(...)        ← domain entity
```

The use case never imports `AsyncSession`, `FastAPI`, or any HTTP concept.

Key Python files:
- `src/usecases/user_usecase.py` — `IUserUsecase` + `UserUsecase`
- `src/usecases/crud_usecase.py` — `ICRUDUsecase` + `CrudUsecase`

### 3. Interface Layer

**Depends on: Use Cases + Domain.** Adapts external I/O into the use case language.

Two sub-components:

**Handlers** — translate HTTP requests/responses to use case calls:
- `src/interface/handlers/user.py` — 5 user routes
- `src/interface/handlers/crud.py` — 3 CRUD routes
- `src/interface/handlers/monitor.py` — health check

**Repository Implementations** — translate database I/O into the repository interface:
- `src/interface/repositories/postgres/user_repository.py` — `PostgresUserRepository`
- `src/interface/repositories/postgres/crud_repository.py` — `PostgresCRUDRepository`
- `src/interface/repositories/mongodb/crud_repository.py` — `MongoDBCRUDRepository`
- `src/interface/repositories/crud_factory.py` — slug → repository dispatch

### 4. Infrastructure Layer (outermost)

**Wires everything together.** Framework configuration, DB connectors, DI setup.

- `src/infrastructure/database/postgres.py` — async SQLAlchemy engine + `get_session()` generator
- `src/infrastructure/database/mongodb.py` — Motor client + `get_collection()`
- `src/infrastructure/server/dependencies.py` — FastAPI `Depends()` factories
- `src/infrastructure/server/middlewares.py` — `jwt_auth` dependency
- `src/infrastructure/server/modules.py` — route registration
- `main.py` — app factory, CORS, lifespan

---

## Dependency Injection

### Go — Manual Constructor Injection

```go
// main.go
postgresHandler := postgres.NewPostgresHandler(cfg)
userRepo := userRepo.NewUserRepository(postgresHandler)
userUsecase := userUsecase.NewUserUsecase(userRepo)
app := application.ApplicationEntity{UserUsecase: userUsecase}
server.NewServer(cfg, app).Start()
```

### Python — FastAPI `Depends()`

```python
# dependencies.py
async def get_user_repository(session=Depends(get_session)):
    return PostgresUserRepository(session)

async def get_user_usecase(repo=Depends(get_user_repository)):
    return UserUsecase(repo)

# handler
@router.post("/login")
async def user_login(body: UserLoginRequest, usecase=Depends(get_user_usecase)):
    return await usecase.user_login(body)
```

FastAPI resolves the dependency graph automatically per request. This makes unit testing trivial — override any dependency:

```python
app.dependency_overrides[get_user_usecase] = lambda: MockUserUsecase()
```

---

## CRUD Generic Module

The generic CRUD module exposes any registered SQLAlchemy model via a REST API without writing any extra code. The pattern mirrors Go's `EntitiyModels` registry.

### Slug derivation

```
Table name  →  snake_case  →  replace _ with -
users       →  users       →  users
user_tokens →  user_tokens →  user-tokens
```

### Factory dispatch

```python
# crud_factory.py
def get_crud_repository(slug: str, session) -> ICRUDRepository:
    model_class = _SLUG_TO_MODEL[slug]        # raises ValueError if unknown
    if model_class.datasource() == "mongodb":
        return MongoDBCRUDRepository(collection, model_class)
    return PostgresCRUDRepository(session, model_class)
```

Both `PostgresCRUDRepository` and `MongoDBCRUDRepository` implement the same `ICRUDRepository` interface — the handler doesn't know which DB it's talking to.

### Schema generation

Python uses SQLAlchemy mapper inspection (`sa_inspect`) to generate Avro-like schemas, replacing Go's reflection-based `GenerateAvroSchema`:

```python
def generate_avro_schema(model_class) -> dict:
    mapper = sa_inspect(model_class)
    fields = [
        {"name": col.key, "type": _sa_type_to_avro(col.type)}
        for col in mapper.columns
        if col.key != "password"
    ]
    return {"type": "record", "name": model_class.__tablename__, "fields": fields}
```

---

## Stateful JWT Authentication

Both implementations use stateful JWT — the token must exist in the database.

```
                    ┌──────────────┐
request ──────────► │  jwt_auth    │
                    │  dependency  │
                    └──────┬───────┘
                           │ 1. Extract Bearer token
                           │ 2. jwt.decode() — verify signature + expiry
                           │ 3. SELECT FROM user_tokens
                           │    WHERE user_id = ? AND access = ?
                           │ 4. If not found → 401
                           │ 5. Set request.state.user
                           ▼
                    ┌──────────────┐
                    │   handler    │
                    └──────────────┘
```

This means `logout` truly invalidates the token — deleting the row from `user_tokens` immediately revokes access for any client holding that token, even if the JWT hasn't expired yet.

---

## Key Design Decisions

### 1. `UserUsecase` calls `PostgresUserRepository.verify_password` directly

In Go, `BcryptHashing` and `CompareHashAndPassword` are methods on the request struct. In Python, they're static methods on `PostgresUserRepository`. The use case calls these directly rather than adding them to the `IUserRepository` interface — keeping the interface focused on DB operations only.

### 2. `selectinload` instead of `join` for relationships

SQLAlchemy 2.0 async doesn't support lazy loading (raises `MissingGreenlet`). All relationship access uses `selectinload()` in the query:

```python
select(UserTokenModel).options(selectinload(UserTokenModel.user))
```

### 3. `repeat_token` — Go bug fixed

Go's `newRefreshToken()` reads `JWT_ACCESS_EXPIRES` for the refresh token expiry (copy-paste bug). Python correctly reads `JWT_REFRESH_EXPIRES`.

### 4. `GET /users/profile` instead of `POST`

Go uses `POST /users/profile` — likely a mistake. Python corrects this to `GET` (idempotent read, no request body).

### 5. Alembic over AutoMigrate

Go uses GORM `AutoMigrate` (implicit, runs at startup). Python uses Alembic explicit migrations — reviewable, versioned, and reversible. The `entrypoint.sh` runs `alembic upgrade head` automatically on container start.
