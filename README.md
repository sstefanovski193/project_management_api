# Project Management API

FastAPI backend for managing users, projects, tasks, task assignments, and comments. The application uses PostgreSQL for persistence, SQLAlchemy for data access, and Alembic for schema migrations.

## Implemented Features

- User registration and user lookup/listing with pagination, sorting, and application-role filtering
- OAuth2 password login with JWT bearer access tokens
- Project creation, lookup, listing, and deletion
- Project membership management with manager and member roles
- Task creation, lookup, listing, updates, deletion, filtering, sorting, and assignee management
- Task comments with project-member access, author-only editing, and author-or-manager deletion
- Automatic validation through FastAPI and Pydantic schemas

The API currently exposes the following route groups:

| Area | Routes |
| --- | --- |
| Authentication | `POST /auth/login` |
| Users | `POST /users`, `GET /users`, `GET /users/{user_id}`, `DELETE /users/{user_id}` |
| Projects | `POST /projects`, `GET /projects`, `GET /projects/{project_id}`, `DELETE /projects/{project_id}` |
| Project members | `POST /projects/{project_id}/members`, `DELETE /projects/{project_id}/members/{user_id}` |
| Tasks | `POST /projects/{project_id}/tasks`, `GET /tasks`, `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`, `DELETE /tasks/{task_id}` |
| Task assignees | `POST /tasks/{task_id}/assignees`, `DELETE /tasks/{task_id}/assignees/{user_id}` |
| Comments | `POST /tasks/{task_id}/comments`, `GET /comments/{comment_id}`, `PATCH /comments/{comment_id}`, `DELETE /comments/{comment_id}` |

The root endpoint, `GET /`, returns a basic API welcome message.

## Technology Stack

- Python 3.10 or newer
- FastAPI
- SQLAlchemy
- PostgreSQL 16 with psycopg
- Alembic
- Pydantic Settings
- PyJWT
- pwdlib[argon2] for password hashing
- pytest automated testing

## Project Structure

```text
app/
├── main.py
├── config.py
├── models.py
├── security.py
├── db/database.py
├── dependencies/authorization.py
│
├── routers/
├── schemas/
└── services/
alembic/
├── env.py
└── versions/
tests/
docs/database-design.md
compose.yaml
```

## Authentication and Authorization

Users authenticate with `POST /auth/login` using OAuth2 form fields named `username` and `password`. The response contains a bearer JWT. Tokens contain the user UUID in the `sub` claim and expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (30 minutes by default).

Passwords are hashed with `pwdlib` using its recommended Argon2 configuration. Application roles are `USER` and `ADMIN`; registration always creates a `USER`, and the API does not provide an endpoint for promoting a user to `ADMIN`.

Project memberships have `MANAGER` and `MEMBER` roles:

- Authenticated users can create projects; the creator becomes the project manager.
- Project managers can add and remove project members.
- Project members can view project details, create and manage tasks, assign project members to tasks, and create or view comments in the project.
- Comment authors can edit comments. Comment authors and project managers can delete comments.
- Application administrators can delete users and projects. A project containing tasks cannot be deleted.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- A PostgreSQL database, either supplied by Docker Compose or available separately

## Local Setup

Create and activate a virtual environment, then install the project and its test dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

Copy the environment templates and adjust the values as needed:

```bash
cp .env.example .env
cp .env.test.example .env.test
```

`.env` contains the local development configuration and the PostgreSQL
credentials used by Docker Compose.

Tests use the separate `.env.test` configuration. The pytest setup selects the
test environment automatically before importing the application.

## Docker and PostgreSQL

The Compose file starts two PostgreSQL 16 services:

- `database` on `localhost:5432` for local development
- `test_database` on `localhost:5433` for tests

The database credentials and names are read from `.env`:

```bash
docker compose up -d database test_database
```

Compose starts PostgreSQL only. Run the FastAPI application separately from the host environment.

To stop the containers:

```bash
docker compose down
```

## Database Migrations

Alembic reads `DATABASE_URL` through `app.config.settings`. With the development database running and `.env` configured, apply all migrations with:

```bash
alembic upgrade head
```

The migration history defines the database schema and its incremental changes.

## Run the Application

From the project root, with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

## API Documentation

FastAPI generates interactive and reference documentation from the registered routes and schemas:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Testing

Tests run against a separate PostgreSQL database.

Start the test database:

```bash
docker compose up -d test_database
```

Run the test suite:

```bash
python -m pytest -v
```

The pytest configuration automatically selects the test environment and uses .env.test.

## Database Design

The relational model, constraints, indexes, relationships, and deletion
behavior are documented in
[docs/database-design.md](docs/database-design.md).