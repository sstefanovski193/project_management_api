# Requirements

## 1. Application

The application is used for creating and managing projects, creating and managing tasks within those projects, and assigning tasks to users.

## 2. Users

The application is intended for individuals and teams within an organization who need to organize projects and tasks.

Only authenticated users will be able to interact with projects and tasks.

## 3. User capabilities

A user can:

* Create projects
* Update projects they own/manage
* Delete projects they own/manage
* Join projects
* Create tasks within projects
* Assign tasks to users who belong to the project
* Update tasks within projects they belong to
* Add comments to tasks

## 4. Project managers

A project manager can:

* Create a project
* Add users to a project
* Remove users from a project
* Update the project name and description
* Delete the project
* Manage project member roles

Project roles are associated with a user's membership in a specific project rather than being global user roles.

## 5. Tasks

A task:

* Belongs to one project
* Has one creator
* Can have multiple assignees
* Has a status
* Has a priority
* Can have multiple comments

## 6. Comments

A comment:

* Belongs to one task
* Has one author
* Contains text
* Records when it was created and updated

## 7. Initial user roles

The first version will have two project-level roles:

* MANAGER
* MEMBER

A user may have different roles in different projects.

For example, a user can be a manager of one project while being a member of another.

## 8. Initial API capabilities

The first version of the API should support:

### Users

* Registration
* Login
* Authentication

### Projects

* Create
* Read
* Update
* Delete
* Add/remove members

### Tasks

* Create tasks
* Read tasks
* Update tasks
* Delete tasks
* Change task status
* Change priority
* Assign tasks to users

### Comments

* Create comments
* Read comments
* Update comments
* Delete comments

The exact API endpoints and permissions will be defined during implementation.

### Design

users
─────────────────────────────────
id                UUID PK
username          VARCHAR NOT NULL UNIQUE
email             VARCHAR NOT NULL UNIQUE
password_hash     VARCHAR NOT NULL
application_role  ENUM NOT NULL
created_at        TIMESTAMP NOT NULL

projects
──────────────────────────────
id           UUID PK
name         VARCHAR NOT NULL
description  TEXT
created_at   TIMESTAMP NOT NULL
updated_at   TIMESTAMP NOT NULL

project_members
────────────────────────────────
user_id       UUID FK NOT NULL
project_id    UUID FK NOT NULL
role          ENUM NOT NULL
joined_at     TIMESTAMP NOT NULL

UNIQUE(user_id, project_id)

tasks
────────────────────────────────
id            UUID PK
project_id    UUID FK NOT NULL
creator_id    UUID FK NULL
title         VARCHAR NOT NULL
description   TEXT
status        ENUM NOT NULL
priority      ENUM NOT NULL
created_at    TIMESTAMP NOT NULL
updated_at    TIMESTAMP NOT NULL

task_assignees
──────────────────────────
task_id       UUID FK NOT NULL
user_id       UUID FK NOT NULL

UNIQUE(task_id, user_id)

comments
────────────────────────────────
id           UUID PK
task_id      UUID FK NOT NULL
user_id      UUID FK NULL
content      TEXT NOT NULL
created_at   TIMESTAMP NOT NULL
updated_at   TIMESTAMP NOT NULL

users
    project_members.user_id
    tasks.creator_id
    task_assignees.user_id
    comments.user_id


projects
    project_members.project_id
    tasks.project_id


tasks
    task_assignees.task_id
    comments.task_id

## Design Decisions

### ID Strategy

UUIDs will be used as primary keys for application entities.

### Task Status

Tasks will initially support three statuses:

- TODO
- IN_PROGRESS
- DONE

### Task Priority

Tasks will initially support three priority levels:

- LOW
- MEDIUM
- HIGH

### Project Roles

Projects will initially support two roles:

- MANAGER
- MEMBER

Roles are associated with project membership rather than being global user roles.

### User Roles

- ADMIN
- USER

### User Uniqueness

Both username and email will be unique.

Email uniqueness ensures that a single email address cannot be associated with multiple user accounts.

Username uniqueness provides users with an unambiguous identity within the application and prevents confusion when users are displayed to other members.

## Constraints To Implement

The following constraints will be enforced by the database:

- User email must be unique
- User username must be unique
- ProjectMember user/project combination must be unique
- TaskAssignee task/user combination must be unique
- Foreign keys must reference existing records

## Business Rules

### Project creation

When an authenticated user creates a project:

1. A Project record is created.
2. A ProjectMember record is created for the creator.
3. The creator is assigned the MANAGER role.
4. Both operations must succeed or fail together.

### Project membership

A user can belong to a project through a ProjectMember record.

A user/project combination can only occur once.

### Task creation

A task:

1. Must belong to an existing project.
2. Must have exactly one creator.
3. Can have multiple assignees.

### Task assignment

A task can only be assigned to users who are members of the task's project.

### Comments

A comment:

1. Must belong to an existing task.
2. Must have one author.
3. The author must be a member of the project containing the task.

## Delete Behavior

| Relationship               | On deletion |
| -------------------------- | ----------- |
| ProjectMember.user_id      | CASCADE     |
| ProjectMember.project_id   | CASCADE     |
| TaskAssignee.user_id       | CASCADE     |
| TaskAssignee.task_id       | CASCADE     |
| Comment.user_id            | SET NULL    |
| Comment.task_id            | CASCADE     |
| Task.creator_id            | SET NULL    |
| Task.project_id            | RESTRICT    |

## Indexes

tasks.project_id
tasks.creator_id
project_members.project_id
task_assignees.user_id
comments.task_id
