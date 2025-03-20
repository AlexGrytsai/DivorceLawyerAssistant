import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.v1.check_pdf_forms.router import router_pdf_check
from src.core import settings

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(router_pdf_check)

app.mount(
    f"/{settings.STATIC_DIR}",
    StaticFiles(directory=settings.STATIC_DIR),
    name="uploads",
)
