# filename: app/schemas/models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class IngestResponse(BaseModel):
    session_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    session_id: str
    status: Literal["processing", "faq_processing", "ready", "error"]
    message: str

class ChatRequest(BaseModel):
    question: str = Field(..., examples=["What is the main topic of the document?"])

class ChatResponse(BaseModel):
    answer: str
    resources: List[Dict[str, Any]]

class FAQGenerationResponse(BaseModel):
    session_id: str
    status: str
    message: str

class SessionData(BaseModel):
    user_session_id: str
    input_type: str | None = None
    input_value: str | None = None
    processed_content: str | None = None
    pdf_file_content_b64: str | None = None
    
    generated_faqs: List[Dict[str, str]] = []
    chat_history: List[Dict[str, Any]] = []
    
    context_is_ready: bool = False
    active_namespaces: List[str] = []
    
    status: Literal["processing", "faq_processing", "ready", "error"] = "processing"
    message: str = "Session initialized."