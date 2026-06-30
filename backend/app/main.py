from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, get_db
from .routers import (
    admin,
    audit,
    boms,
    changes,
    dashboard,
    documents,
    foundation,
    integration,
    materials,
    processes,
    products,
    projects,
    quality,
    reports,
    requirements,
    session,
    workbench,
    workflow,
)
from .services.bootstrap import ensure_lightweight_schema, ensure_admin

app = FastAPI(title="SemiPLM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(admin.router)
app.include_router(foundation.router)
app.include_router(workflow.router)
app.include_router(products.router)
app.include_router(materials.router)
app.include_router(requirements.router)
app.include_router(boms.router)
app.include_router(documents.router)
app.include_router(workbench.router)
app.include_router(processes.router)
app.include_router(changes.router)
app.include_router(projects.router)
app.include_router(quality.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(integration.router)
app.include_router(audit.router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_lightweight_schema()
    db = next(get_db())
    try:
        ensure_admin(db)
    finally:
        db.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
