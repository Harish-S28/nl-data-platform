from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, query

app = FastAPI(title="NL Data Analysis Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
