import os

import uvicorn
from dotenv import load_dotenv

from create_app import create_app

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


def main() -> int:
    load_dotenv()
    app = create_app()
    host = os.getenv("HTTP_HOST", DEFAULT_HOST)
    port = int(os.getenv("HTTP_PORT", str(DEFAULT_PORT)))
    uvicorn.run(app, host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
