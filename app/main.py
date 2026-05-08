# uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.saved_links import router as saved_links_router
from app.routes.users import router as users_router

from app.routes.crawl_jobs import router as crawl_jobs_router

from app.routes.tags import router as tags_router

from app.routes.collections import router as collections_router

from app.routes.auth import router as auth_router

app = FastAPI(title="Link Archive API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend server is running",
    }


app.include_router(users_router)
app.include_router(auth_router)
app.include_router(saved_links_router)
app.include_router(crawl_jobs_router)
app.include_router(tags_router)
app.include_router(collections_router)
