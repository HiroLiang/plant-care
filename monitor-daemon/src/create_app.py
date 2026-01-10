from fastapi import FastAPI
from contextlib import asynccontextmanager
from uvicorn import lifespan

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
    return app
