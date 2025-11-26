from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers import auth, projects, workflows, executions, telemetry

load_dotenv()

app = FastAPI(
    title="Agora Cloud API",
    description="Workflow-as-a-Service platform for Agora framework",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(telemetry.router)

@app.get("/")
async def root():
    return {
        "message": "Agora Cloud API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
