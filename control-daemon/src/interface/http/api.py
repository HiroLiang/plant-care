from fastapi import FastAPI

from interface.http.routers import controls, daemon


def register_routers(app: FastAPI) -> None:
    app.include_router(daemon.router)
    app.include_router(controls.router)
