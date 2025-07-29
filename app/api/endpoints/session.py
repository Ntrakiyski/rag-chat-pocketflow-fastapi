import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Body
from app.schemas.models import SessionData
from app.core.session import get_session, update_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/session/{session_id}", response_model=SessionData, status_code=status.HTTP_200_OK)
async def get_session_data(session_id: str):
    logger.info(f"Retrieving session data for session: {session_id}")
    session_data = get_session(session_id)
    if not session_data:
        logger.warning(f"Attempted to retrieve non-existent session: {session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session_data

@router.put("/session/{session_id}", response_model=SessionData, status_code=status.HTTP_200_OK)
async def update_session_data(session_id: str, updates: Dict[str, Any] = Body(
    ...,
    examples=[
        {"chat_history": []},
        {"status": "ready", "message": "Manually set to ready"},
        {"context_is_ready": False}
    ]
)):
    logger.info(f"Updating session {session_id} with updates: {updates}")
    updated_session_data = update_session(session_id, updates)
    if not updated_session_data:
        logger.warning(f"Attempted to update non-existent session: {session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    
    logger.info(f"Session {session_id} updated successfully.")
    return updated_session_data
