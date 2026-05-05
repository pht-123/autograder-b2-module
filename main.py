from __future__ import annotations

from fastapi import FastAPI

from api_and_client.api_and_client import router

from core.app_state import build_app_state, shutdown_app_state
from middleware.exception_handler import install_exception_handlers
from middleware.request_logging import install_request_logging


def create_app() -> FastAPI:
    app = FastAPI(title="AutoGrader B2", version="0.1.0")

    install_request_logging(app)
    install_exception_handlers(app)

    app.include_router(router)

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.b2 = await build_app_state()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        # Best-effort cleanup of background tasks and HTTP clients.
        b2 = getattr(app.state, "b2", None)
        if b2 is not None:
            await shutdown_app_state(b2)

    return app


app = create_app()

# ===================== 服务启动 =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)