from fastapi import FastAPI
from routes import router
from qseckey.utils.config import settings
import uvicorn
import threading
import logging



if __name__ == "__main__":
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    app.include_router(router)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
