# filename: app/api/endpoints/faq.py

from fastapi import APIRouter, HTTPException, status
from app.schemas.models import FAQGenerationResponse
from app.workers.tasks import run_faq_generation_flow
from app.core.session import get_session, update_session # Import update_session for setting status
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/faq/generate/{session_id}", response_model=FAQGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_faq(session_id: str):
    """
    Initiates an asynchronous job to generate FAQs for an already ingested session.
    This enhances the session's context for future chat queries.
    """
    session_data = get_session(session_id)
    if not session_data:
        logger.warning(f"FAQ generation requested for non-existent session: {session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    if not session_data.context_is_ready:
        logger.warning(f"FAQ generation requested for session {session_id} but content is not ready.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content is not ready. Cannot generate FAQs.")

    # Update session status to indicate FAQ generation is in progress
    update_session(session_id, {"status": "faq_processing", "message": "FAQ generation in progress."})
    logger.info(f"Dispatching FAQ generation task for session: {session_id}")

    # Dispatch the background task.
    run_faq_generation_flow.delay(session_id)

    return FAQGenerationResponse(
        session_id=session_id,
        status="faq_processing",
        message="FAQ generation has started."
    )