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
