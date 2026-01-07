from fastapi import FastAPI
from interface.http.routers import daemon, monitors


def register_routers(app: FastAPI):
    app.include_router(daemon.router)
    app.include_router(monitors.router)
