# filename: app/workers/tasks.py

import logging
import tempfile
import base64
import os
from app.workers.celery_app import celery_app
from app.flows import create_setup_flow, create_faq_flow
from app.core.session import get_session, update_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task
def run_ingestion_flow(shared_data: dict):
    session_id = shared_data.get("user_session_id")
    input_type = shared_data.get("input_type")
    logger.info(f"Starting ingestion task for session_id: {session_id}, type: {input_type}")

    temp_pdf_path = None
    try:
        if input_type == "pdf" and shared_data.get("pdf_file_content_b64"):
            pdf_bytes = base64.b64decode(shared_data["pdf_file_content_b64"])
            fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            with open(temp_pdf_path, 'wb') as temp_pdf:
                temp_pdf.write(pdf_bytes)
            
            shared_data["original_filename"] = shared_data["input_value"]
            shared_data["input_value"] = temp_pdf_path
        
        setup_flow = create_setup_flow()
        setup_flow.run(shared_data)

    except Exception as e:
        logger.error(f"Error in ingestion flow for session_id: {session_id}: {e}", exc_info=True)
        update_session(session_id, {"status": "error", "message": str(e)})
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

@celery_app.task
def run_faq_generation_flow(session_id: str):
    logger.info(f"Starting FAQ generation task for session_id: {session_id}")
    
    session_obj = get_session(session_id)
    if not session_obj or not session_obj.context_is_ready:
        update_session(session_id, {"status": "error", "message": "Content not ready for FAQ generation."})
        return

    try:
        shared_data = session_obj.model_dump()
        faq_flow = create_faq_flow()
        faq_flow.run(shared_data)
        update_session(session_id, {"status": "ready", "message": "FAQs generated and context updated."})
    except Exception as e:
        logger.error(f"Error in FAQ generation flow for session_id: {session_id}: {e}", exc_info=True)
        update_session(session_id, {"status": "error", "message": str(e)})