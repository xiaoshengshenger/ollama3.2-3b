

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.api.llm_api.ingest.ingest_service import IngestService
from app.api.llm_api.ingest.model import IngestedDoc


import logging

logger = logging.getLogger(__name__)

ingest_router = APIRouter()

class IngestResponse(BaseModel):
    object: Literal["list"]
    model: Literal["private-gpt"]
    data: list[IngestedDoc]

@ingest_router.post("/file")
def ingest_file(request: Request, file: UploadFile) -> IngestResponse:

    service = request.state.injector.get(IngestService)
    if file.filename is None:
        raise HTTPException(400, "No file name provided")
    ingested_documents = service.ingest_bin_data(file.filename, file.file)
    return IngestResponse(object="list", model="private-gpt", data=ingested_documents)