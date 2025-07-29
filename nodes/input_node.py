# filename: nodes/input_node.py

from pocketflow import Node
from app.core.session import get_session, update_session, create_session # NEW IMPORTS
import uuid
import datetime
import os
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class InputNode(Node):
    def prep(self, shared: dict):
        logger.info("InputNode: Preparing...")

        # user_session_id is now passed from the API endpoint directly in shared_data
        user_session_id = shared.get("user_session_id")
        if not user_session_id:
            # This should ideally not happen if API is working correctly, but as a fallback
            user_session_id = str(uuid.uuid4())
            shared["user_session_id"] = user_session_id
            logger.warning(f"InputNode: user_session_id not found in shared, generated new: {user_session_id}")
        else:
            logger.info(f"InputNode: Using existing session ID: {user_session_id}")

        # Input validation (these values come from the API request in shared)
        input_type = shared.get("input_type")
        input_value = shared.get("input_value")
        
        if input_type == "none":
            logger.info("InputNode: Proceeding with no specific content input.")
            # Update session status directly via app.core.session
            update_session(user_session_id, {"status": "ready", "context_is_ready": False, "message": "No content provided, chat without context."})
            return {"status": "success", "input_type": input_type, "input_value": input_value, "user_session_id": user_session_id}

        if not input_type or not input_value:
            error_message = "Input type or value missing for content processing."
            shared["error_message"] = error_message
            logger.error(error_message)
            update_session(user_session_id, {"status": "error", "message": error_message})
            return {"status": "error", "input_type": None, "input_value": None, "user_session_id": user_session_id}

        if input_type not in ["website", "pdf"]:
            error_message = f"Invalid input type: {input_type}. Must be 'website' or 'pdf'."
            shared["error_message"] = error_message
            logger.error(error_message)
            update_session(user_session_id, {"status": "error", "message": error_message})
            return {"status": "error", "input_type": None, "input_value": None, "user_session_id": user_session_id}

        # Load existing session data (if any) to ensure the node has the latest state
        existing_session_data = get_session(user_session_id) # Use get_session from app.core.session
        if existing_session_data:
            # Merge loaded data into shared_data, prioritizing current shared_data values
            for key, value in existing_session_data.model_dump().items(): # Use model_dump()
                if key not in shared:
                    shared[key] = value
            logger.info(f"InputNode: Loaded existing session data for {user_session_id}")
        else:
            logger.info(f"InputNode: No existing session data found for {user_session_id}.")
            # If session wasn't created by API (e.g., direct node run), create it.
            # This path is less likely in the API flow but good for robustness.
            create_session(input_type=input_type, input_value=input_value) # Use create_session from app.core.session


        # Initialize chat_history if not present in loaded session data
        if "chat_history" not in shared or shared["chat_history"] is None:
            shared["chat_history"] = []
            update_session(user_session_id, {"chat_history": []})
            logger.info("InputNode: Initialized empty chat history.")

        # Add a timestamp to the shared for the current interaction (optional, for logging)
        shared["timestamp"] = datetime.datetime.now().isoformat()

        logger.info("InputNode: Preparation complete.")
        return {"status": "success", "input_type": input_type, "input_value": input_value, "user_session_id": user_session_id}

    def exec(self, prep_res: dict) -> dict:
        logger.info("InputNode: Executing...")
        if prep_res.get("status") == "error":
            return {"status": "error"}

        # No heavy execution needed here, just pass the prepared data
        logger.info("InputNode: Execution complete.")
        return {"status": "success",
                "input_type": prep_res["input_type"],
                "input_value": prep_res["input_value"],
                "user_session_id": prep_res["user_session_id"]}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        logger.info("InputNode: Post-processing...")
        if exec_res.get("status") == "error":
            return "error"

        # Store input type and value in shared for subsequent nodes
        shared["input_type"] = exec_res.get("input_type", "")
        shared["input_value"] = exec_res.get("input_value", "")
        shared["user_session_id"] = exec_res.get("user_session_id")

        logger.info("InputNode: Post-processing complete.")
        return "default"