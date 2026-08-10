# Project Management API

## Application Overview

The application allows users to create and manage projects and the tasks belonging to those projects.

Users can:

* Create and manage projects they own
* Become members of projects
* Create tasks within projects
* Assign tasks to other project members
* Update task status and priority
* Add comments to tasks

Projects have managers and members with different permissions.

## Initial Domain Model

The initial version of the application will contain the following entities:

* User
* Project
* ProjectMember
* Task
* TaskAssignee
* Comment

The detailed requirements and database design are documented separately in the `docs/` directory.

## Development Status

### Phase 1 — Planning and Design

* [x] Define initial application purpose
* [x] Define initial users and use cases
* [x] Define initial domain entities
* [x] Draft database relationships
* [ ] Finalize database design

### Phase 2 — FastAPI

* [ ] Set up FastAPI application
* [ ] Implement initial API endpoints
* [ ] Add request and response validation
* [ ] Add error handling
* [ ] Add dependency injection

### Phase 3 — Database

* [ ] Set up PostgreSQL
* [ ] Implement SQLAlchemy models
* [ ] Add Alembic migrations
* [ ] Implement database operations

### Phase 4 — Authentication and Authorization

* [ ] User registration
* [ ] Password hashing
* [ ] Login
* [ ] JWT authentication
* [ ] Project-level permissions

### Phase 5 — Async Features

* [ ] Identify appropriate asynchronous operations
* [ ] Implement asynchronous database/API operations
* [ ] Practice concurrency with `asyncio`
* [ ] Implement timeout and cancellation handling where appropriate

### Phase 6 — Testing

* [ ] Unit tests
* [ ] API tests
* [ ] Database/integration tests
* [ ] Authentication tests

### Phase 7 — Docker and Finalization

* [ ] Dockerize the application
* [ ] Add Docker Compose
* [ ] Improve logging and configuration
* [ ] Review API documentation
* [ ] Perform a final code and architecture review

