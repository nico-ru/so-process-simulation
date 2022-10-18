from typing import Union
from fastapi import FastAPI, Header
from pydantic.main import BaseModel
from services.utils.config import Settings

from utils.util import log_request

name = "message"
server = FastAPI(title=name)
settings = Settings()  # type: ignore


@server.post(f"/{name}")
def create_invoice(
    data: BaseModel,
    correlation_id: Union[str, None] = Header(),
):
    id = correlation_id or "NA"
    log_request(f"/{name}", data, name, id)
    return dict(success=True)
