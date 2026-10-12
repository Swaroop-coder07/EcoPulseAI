from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import seed
from routers import analytics, resources


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and auto-seed sample campus data on first run.
    seed.run()
    yield


app = FastAPI(
    title="EcoPulse AI",
    description="Smart campus sustainability platform: track, detect and reduce resource waste.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resources.router)
app.include_router(analytics.router)


@app.get("/")
def health():
    return {"app": "EcoPulse AI", "status": "ok", "docs": "/docs"}
