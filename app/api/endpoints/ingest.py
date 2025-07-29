import uuid
import base64
import logging
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.schemas.models import IngestResponse, StatusResponse
from app.workers.tasks import run_ingestion_flow
from app.core.session import create_session, get_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_content(
    pdf_file: UploadFile = File(None),
    web_url: str = Form(None)
):
    if not pdf_file and not web_url:
        raise HTTPException(status_code=400, detail="Either a PDF file or a web URL must be provided.")
    if pdf_file and web_url:
        raise HTTPException(status_code=400, detail="Provide either a PDF file or a web URL, not both.")

    input_type = "pdf" if pdf_file else "website"
    input_value = pdf_file.filename if pdf_file else web_url
    
    session_obj = create_session(input_type=input_type, input_value=input_value)
    
    task_shared_data = session_obj.model_dump()
    
    if pdf_file:
        pdf_content_bytes = await pdf_file.read()
        task_shared_data["pdf_file_content_b64"] = base64.b64encode(pdf_content_bytes).decode('utf-8')

    run_ingestion_flow.delay(task_shared_data)
    
    return IngestResponse(
        session_id=session_obj.user_session_id,
        status="processing",
        message="Content ingestion started. Check status endpoint for progress."
    )

@router.get("/ingest/status/{session_id}", response_model=StatusResponse)
async def get_ingestion_status(session_id: str):
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found.")
    return StatusResponse(
        session_id=session_id,
        status=session_data.status,
        message=session_data.message
    )
