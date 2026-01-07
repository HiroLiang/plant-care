import httpx


class ControlDaemonHttpClient:
    def __init__(self, base_url: str, token: str = ""):
        self.client = httpx.AsyncClient(base_url=base_url)
        self.token = token

    async def close(self):
        await self.client.aclose()
