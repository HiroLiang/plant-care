from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from application.control_service import InvalidControlRequest, UpstreamRequestError, UpstreamUnavailableError
from bootstrap.bootstrap import bootstrap, shutdown
from interface.http.api import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = await bootstrap()
    app.state.ctx = ctx
    yield
    await shutdown(ctx)


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    register_routers(app)

    @app.exception_handler(InvalidControlRequest)
    async def handle_invalid_request(_, exc: InvalidControlRequest) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(UpstreamUnavailableError)
    async def handle_upstream_unavailable(_, exc: UpstreamUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(UpstreamRequestError)
    async def handle_upstream_error(_, exc: UpstreamRequestError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app
