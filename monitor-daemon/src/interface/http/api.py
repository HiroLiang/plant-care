from fastapi import FastAPI
from application.monitor_service import MonitorService


def create_app(service: MonitorService) -> FastAPI:
    app = FastAPI(title="Monitor Daemon")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/status")
    def get_status():
        """
        Read-only snapshot of latest sensor values.
        """
        return service.snapshot()

    return app
