# filename: nodes/content_processing_node.py

import os
from dotenv import load_dotenv
import logging

load_dotenv()

from pocketflow import Node
from app.core.config import MAX_CRAWL_PAGES
from utils.firecrawl_utils import crawl_website
from utils.llamaindex_pdf_extractor import extract_text_from_pdf
from utils.create_embedding import process_and_embed_yaml
# --- CHANGE THIS IMPORT ---
from utils.qdrant_storage import store_embeddings_in_qdrant # Changed from upstash_vector_storage
# --- END CHANGE ---
from app.core.session import get_session, update_session

logger = logging.getLogger(__name__)

class ContentProcessingNode(Node):
    def prep(self, shared: dict):
        logger.info("ContentProcessingNode: Preparing...")
        input_type = shared.get("input_type")
        input_value = shared.get("input_value")
        user_session_id = shared.get("user_session_id")

        if not input_type or not input_value:
            error_message = "Input type or value missing for content processing."
            shared["error_message"] = error_message
            logger.error(error_message)
            update_session(user_session_id, {"status": "error", "message": error_message})
            return {"status": "error"}

        logger.info(f"  Processing input type: {input_type}, value: {input_value}")
        return {"status": "success", "input_type": input_type, "input_value": input_value, "user_session_id": user_session_id}

    def exec(self, prep_res: dict) -> dict:
        logger.info("ContentProcessingNode: Executing...")
        if prep_res.get("status") == "error":
            return {"status": "error", "processed_content": ""}

        input_type = prep_res.get("input_type")
        input_value = prep_res.get("input_value") # This is the temp path or URL
        processed_content = ""

        if input_type == "website":
            crawled_content = crawl_website(url=input_value, max_pages=MAX_CRAWL_PAGES)
            if not crawled_content:
                return {"status": "error", "error_message": "Failed to crawl website."}
            processed_content = crawled_content
        elif input_type == "pdf":
            extracted_content = extract_text_from_pdf(input_value)
            if not extracted_content:
                return {"status": "error", "error_message": "Failed to extract text from PDF."}
            processed_content = extracted_content
        
        return {"status": "success", "processed_content": processed_content}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        logger.info("ContentProcessingNode: Post-processing...")
        user_session_id = prep_res.get("user_session_id")
        input_type = prep_res.get("input_type")
        
        # Use original filename from shared for namespace, not temp path
        source_for_namespace = shared.get("original_filename", prep_res.get("input_value"))

        if exec_res.get("status") == "error":
            error_message = exec_res.get("error_message", "Content processing failed.")
            update_session(user_session_id, {"status": "error", "message": error_message})
            return "error"

        processed_content = exec_res.get("processed_content", "")
        if not processed_content:
            update_session(user_session_id, {"status": "ready", "context_is_ready": False, "message": "No content to process."})
            return "default"

        embedded_chunks = process_and_embed_yaml(processed_content)
        if not embedded_chunks:
            error_message = "Failed to create embeddings."
            update_session(user_session_id, {"status": "error", "message": error_message})
            return "error"

        combined_processed_content = " ".join([chunk['text'] for chunk in embedded_chunks])
        # --- CHANGE THIS FUNCTION CALL ---
        storage_success = store_embeddings_in_qdrant(embedded_chunks, input_type, user_session_id, source=source_for_namespace)
        # --- END CHANGE ---

        if not storage_success:
            error_message = "Failed to store embeddings in vector DB."
            update_session(user_session_id, {"status": "error", "message": error_message})
            return "error"

        update_session(user_session_id, {
            "status": "ready",
            "context_is_ready": True,
            "message": "Content processed and ready for chat.",
            "processed_content": combined_processed_content
        })
        
        return "default"