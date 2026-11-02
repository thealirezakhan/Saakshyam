from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.db import Database
from .modules import (
    admin,
    applications,
    copilot,
    documents,
    evc,
    identity,
    reporting,
    review,
    validation,
    verification,
    workflows,
)


def error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": _code(exc.status_code), "message": exc.detail}},
    )


def _code(status: int) -> str:
    return {
        400: "bad_request", 401: "unauthorized", 403: "forbidden",
        404: "not_found", 409: "conflict", 413: "payload_too_large",
        422: "validation_error", 500: "internal_error",
    }.get(status, "error")


def create_app(db_url: str | None = None, serve_static: bool = True,
               seed_mode: str | None = None) -> FastAPI:
    app = FastAPI(title="AICTE Copilot API", version="1.0.0")
    app.state.db = Database(db_url or settings.DATABASE_URL)
    app.state.db.create_all()
    mode = seed_mode or settings.DEMO_MODE
    app.state.seed_mode = mode
    from .seed import seed_demo_if_empty, seed_if_empty
    session = app.state.db.session()
    try:
        if mode == "aarohan":
            seed_demo_if_empty(session)
        else:
            seed_if_empty(session)
    finally:
        session.close()

    @app.get("/api/health")
    def health():
        return {"data": {"status": "ok", "demo_mode": mode}}

    app.include_router(identity.router)
    app.include_router(applications.router)
    app.include_router(documents.router)
    app.include_router(validation.router)
    app.include_router(verification.router)
    app.include_router(evc.router)
    app.include_router(review.router)
    app.include_router(reporting.router)
    app.include_router(copilot.router)
    app.include_router(workflows.router)
    app.include_router(admin.router)
    app.exception_handler(HTTPException)(error_handler)

    if serve_static:
        import os
        web_dir = os.path.join(os.path.dirname(__file__), "..", "..", "web")
        if os.path.isfile(os.path.join(web_dir, "index.html")):
            app.mount("/", StaticFiles(directory=os.path.abspath(web_dir), html=True), name="web")
    return app


app = create_app()
