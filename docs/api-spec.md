# API Specification

**Base URL:** `http://localhost:8000`  
**API Prefix:** `/api/v1`  
**Auth scheme:** HTTP Bearer JWT  
**Content-Type:** `application/json`

Interactive docs: **http://localhost:8000/docs** (Swagger UI) | **http://localhost:8000/redoc**

---

## Error Response Shape

All `4xx` errors return the same envelope:

```json
{
  "trace_id": "string",
  "message": "string"
}
```

| Trace ID | Endpoint | Meaning |
|---|---|---|
| `users-001` | `POST /users/register` | Validation or DB error on register |
| `users-002` | `POST /users/login` | User not found or wrong password |
| `users-003` | `POST /users/refresh-token` | Token expired, invalid, or not in DB |
| `users-004` | `POST /users/logout` | Token not found or invalid |
| `middleware-002` | Any protected route | Missing, invalid, or revoked access token |
| `error` | Any CRUD route | Slug not found or record not found |

---

## Health Check

### `GET /api/v1/`

No authentication required.

**Response 200**
```json
{
  "name": "Python Clean Architecture API",
  "version": "1.0.0"
}
```

---

## Users

### `POST /api/v1/users/register`

Create a new user account.

**Request body**
```json
{
  "email": "user@example.com",
  "password": "plaintext_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

| Field | Type | Validation |
|---|---|---|
| `email` | string | Must match `^[\w\-.]+@([\w\-]+\.)+[\w\-]{2,4}$` |
| `password` | string | Required, stored as bcrypt hash (cost 10) |
| `first_name` | string | Required |
| `last_name` | string | Required |

**Response 201**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Response 400**
```json
{ "trace_id": "users-001", "message": "email pattern is invalid" }
```

**Response 422** — Pydantic validation failure (missing fields, wrong types)

---

### `POST /api/v1/users/login`

Authenticate and receive JWT tokens.

**Request body**
```json
{
  "email": "user@example.com",
  "password": "plaintext_password"
}
```

**Response 200**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  },
  "token": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

**Response 400**
```json
{ "trace_id": "users-002", "message": "password is invalid" }
```

---

### `POST /api/v1/users/logout`

Invalidate the current session by deleting the token row from the database.

**Request body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200**
```json
null
```

**Response 400**
```json
{ "trace_id": "users-004", "message": "user token not found" }
```

---

### `POST /api/v1/users/refresh-token`

Exchange a refresh token for a new access token. The refresh token's original expiry is **never extended** (`RepeatToken` pattern from the Go implementation).

**Request body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200** — same shape as login
```json
{
  "user": { ... },
  "token": {
    "access": "eyJ...(new access token)",
    "refresh": "eyJ...(re-signed, same expiry)"
  }
}
```

**Response 400**
```json
{ "trace_id": "users-003", "message": "token had expired" }
```

---

### `GET /api/v1/users/profile`

Return the authenticated user's profile. Requires a valid Bearer access token.

**Headers**
```
Authorization: Bearer eyJ...
```

**Response 200**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Response 401**
```json
{ "trace_id": "middleware-002", "message": "missing authorization header" }
```

> **Note:** The Go API used `POST /users/profile` — this is corrected to `GET` in the Python implementation.

---

## CRUD Data Explorer

All endpoints require Bearer JWT. The `{slug}` is derived from the model's table name: `snake_case` → replace `_` with `-`.

### Registered Slugs

| Slug | Model | Table | Datasource |
|---|---|---|---|
| `users` | `UserModel` | `users` | PostgreSQL |
| `user-tokens` | `UserTokenModel` | `user_tokens` | PostgreSQL |
| `user-permissions` | `UserPermissionModel` | `user_permissions` | PostgreSQL |

---

### `GET /api/v1/data/{slug}/describe`

Returns an Avro-like schema describing the model's fields.

**Headers**
```
Authorization: Bearer eyJ...
```

**Response 200**
```json
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

> `password` is always excluded from the schema.

**Response 400**
```json
{ "trace_id": "error", "message": "entity model slug 'bad-slug' not found. Available: user-permissions, user-tokens, users" }
```

---

### `GET /api/v1/data/{slug}/`

Paginated list of all records for a model.

**Headers**
```
Authorization: Bearer eyJ...
```

**Query parameters**

| Param | Type | Default | Max | Description |
|---|---|---|---|---|
| `_page` | int | `1` | — | Page number (1-indexed) |
| `_pageSize` | int | `10` | `1000` | Records per page |

**Response 200**
```json
{
  "code": 200,
  "data": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 10,
  "total_page": 1,
  "total_data": 1,
  "message": "success",
  "data_schema": {
    "type": "record",
    "name": "users",
    "fields": [...]
  }
}
```

---

### `GET /api/v1/data/{slug}/{id}`

Fetch a single record by primary key (PostgreSQL) or ObjectId (MongoDB).

**Headers**
```
Authorization: Bearer eyJ...
```

**Response 200**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  },
  "message": "success",
  "data_schema": {
    "type": "record",
    "name": "users",
    "fields": [...]
  }
}
```

**Response 400**
```json
{ "trace_id": "error", "message": "record '999' not found" }
```

---

## JWT Token Details

| Property | Access Token | Refresh Token |
|---|---|---|
| Algorithm | HS256 | HS256 |
| Subject (`sub`) | `access-token` | `refresh-token` |
| Audience (`aud`) | `["user", "admin"]` | `["user", "admin"]` |
| Default expiry | 86400s (1 day) | 172800s (2 days) |
| Env var | `JWT_ACCESS_EXPIRES` | `JWT_REFRESH_EXPIRES` |
| Issuer (`iss`) | `app_name.lower()` | `app_name.lower()` |

**Custom claims nested under `"claims"` key:**
```json
{ "claims": { "id": 1 } }
```

**Stateful validation:** After decoding, the token string is looked up in the `user_tokens` table. A valid JWT signature is not sufficient — the token must also exist in the database.
