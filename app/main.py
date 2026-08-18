from fastapi import FastAPI

from app.routers import projects, users

app = FastAPI()

app.include_router(users.router)
app.include_router(projects.router)


@app.get("/")
async def root():
    return {"message": "Project Management API"}
