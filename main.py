from fastapi import FastAPI
from routes import router
from qseckey.utils.config import settings
import uvicorn
import threading
import logging


if __name__ == "__main__":
    # Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create and start FastAPI app
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    app.include_router(router)

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
