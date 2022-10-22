from typing import Union
from fastapi import FastAPI, Header, Request
from services.utils.config import Settings

from services.utils.util import get_logger, log_event

name = "message"
server = FastAPI(title=name)
settings = Settings()  # type: ignore
logger = get_logger(name)


@server.post(f"/{name}")
async def create_invoice(
    request: Request,
    correlation_id: Union[str, None] = Header(),
):
    id = correlation_id or "NA"
    body = b""
    async for chunk in request.stream():
        body += chunk
    log_event(f"/{name}", body.decode("utf-8"), name, id, type="req")
    return dict(success=True)
