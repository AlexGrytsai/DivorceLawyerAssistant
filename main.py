import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.api.v1.check_pdf_forms.router import router_pdf_check
from src.api.v1.cloud_storage import router as router_cloud_storage
from src.core import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Divorce Lawyer Assistant API", version="1.0.0")

app.include_router(router_pdf_check)
app.include_router(router_cloud_storage)

app.mount(
    f"/{settings.STATIC_DIR}",
    StaticFiles(directory=settings.STATIC_DIR),
    name="static",
)

templates = Jinja2Templates(directory=Path("src/templates"))


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/data-for-rag", response_class=HTMLResponse)
async def serve_cloud_storage_ui(request: Request):
    return templates.TemplateResponse(
        "data_for_rag.html", {"request": request}
    )
