import os
import uvicorn

from dotenv import load_dotenv
from create_app import create_app

# load env
load_dotenv()


def main():
    app = create_app()

    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", "8001"))

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
