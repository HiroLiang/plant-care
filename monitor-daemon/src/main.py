import os
import uvicorn

from pathlib import Path
from dotenv import load_dotenv
from create_app import create_app

# load env
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def main():
    app = create_app()

    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", "8001"))

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
