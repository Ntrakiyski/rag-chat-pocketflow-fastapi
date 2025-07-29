import logging
from fastapi import APIRouter, HTTPException, status, Body
from app.schemas.models import ChatRequest, ChatResponse, SessionData
from app.core.session import get_session, update_session
from nodes.chat_query_node import ChatQueryNode

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat/{session_id}", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_content(session_id: str, request: ChatRequest = Body(...)):
    logger.info(f"Received chat request for session: {session_id} with question: '{request.question}'")

    session_obj: SessionData = get_session(session_id)
    if not session_obj:
        logger.warning(f"Chat request for non-existent session: {session_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    if not session_obj.context_is_ready:
        logger.warning(f"Chat request for session {session_id} but content is not ready.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content is not ready for chat. Please wait for ingestion to complete.")

    chat_node = ChatQueryNode()

    shared_data_for_node = session_obj.model_dump()
    shared_data_for_node["user_query"] = request.question

    try:
        prep_res = chat_node.prep(shared_data_for_node)
        
        answer, resources, action = chat_node.exec(prep_res)
        
        post_action = chat_node.post(shared_data_for_node, prep_res, (answer, resources, action))

        if post_action == "error":
            error_message = shared_data_for_node.get("error_message", "An unknown error occurred during chat processing.")
            logger.error(f"Chat node returned error for session {session_id}: {error_message}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
        
        if post_action == "exit":
            logger.info(f"Chat node requested exit for session {session_id}.")
            pass

    except Exception as e:
        logger.error(f"Unexpected error during chat processing for session {session_id}: {e}", exc_info=True)
        update_session(session_id, {"status": "error", "message": f"An unexpected server error occurred: {e}"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

    return ChatResponse(answer=answer, resources=resources)
