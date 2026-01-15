

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, UploadFile
from pydantic import BaseModel

from backend_app.api.llm_api.ingest.ingest_service import IngestService
from backend_app.api.llm_api.ingest.model import IngestedDoc
from backend_app.api.llm_api.ingest.ingest_service_kg_rag import Neo4jKGRAGService


import logging

logger = logging.getLogger(__name__)

ingest_router = APIRouter()

class IngestResponse(BaseModel):
    object: Literal["list"]
    model: Literal["private-gpt"]
    data: list[IngestedDoc]
    data_kg: list[IngestedDoc]

@ingest_router.post("/file")
def ingest_file(request: Request, file: UploadFile) -> IngestResponse:

    service = request.state.injector.get(IngestService)
    if file.filename is None:
        raise HTTPException(400, "No file name provided")
    #rag
    ingested_documents = service.ingest_bin_data(file.filename, file.file)
    #kg_rag
    kg_service = request.state.injector.get(Neo4jKGRAGService)
    ingested_documents_kg_rag = kg_service.ingest_bin_data(file.filename, file.file)
    #logger.info(f"Ingested: {ingested_documents} --------------ingested_documents_kg_rag: {ingested_documents_kg_rag} ")
    return IngestResponse(object="list", model="private-gpt", data=ingested_documents, data_kg=
                          ingested_documents_kg_rag)


@ingest_router.get("/list")
def list_ingested(request: Request) -> IngestResponse:

    service = request.state.injector.get(IngestService)
    #rag
    ingested_documents = service.list_ingested()
    #kg_rag
    kg_service = request.state.injector.get(Neo4jKGRAGService)
    ingested_documents_kg_rag = kg_service.list_ingested_kg_docs()
    logger.info(f"向量数据库: {ingested_documents} --------------知识图谱: {ingested_documents_kg_rag} ")
    return IngestResponse(object="list", model="private-gpt", data=ingested_documents, data_kg=ingested_documents_kg_rag)


@ingest_router.delete("/{doc_id}/{kg_docId}")
def delete_ingested(request: Request, doc_id: str, kg_docId: str) -> None:

    service = request.state.injector.get(IngestService)
    service.delete(doc_id) 

    kg_service = request.state.injector.get(Neo4jKGRAGService)
    kg_service.delete_kg_doc(kg_docId)