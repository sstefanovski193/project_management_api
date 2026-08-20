from fastapi import FastAPI

from app.routers import projects, users, tasks

app = FastAPI()

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(tasks.project_task_router)


@app.get("/")
async def root():
    return {"message": "Project Management API"}
