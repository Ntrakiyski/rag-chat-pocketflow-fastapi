# filename: nodes/faq_generation_node.py

from pocketflow import Node
from utils.openrouter_faq_generator import generate_faqs
from app.core.config import NUM_FAQS_TO_GENERATE
# --- CHANGE THIS IMPORT ---
from utils.qdrant_storage import store_embeddings_in_qdrant # Changed from upstash_vector_storage
# --- END CHANGE ---
from utils.create_embedding import create_embedding
from app.core.session import update_session, get_session
import logging

logger = logging.getLogger(__name__)

class FAQGenerationNode(Node):
    def prep(self, shared: dict):
        logger.info("FAQGenerationNode: Preparing...")
        processed_content = shared.get("processed_content")
        user_session_id = shared.get("user_session_id")
        input_type = shared.get("input_type")
        input_value = shared.get("input_value")

        update_session(user_session_id, {"status": "faq_processing", "message": "FAQ generation in progress."})

        if not processed_content:
            error_message = "No processed content available for FAQ generation."
            shared["error_message"] = error_message
            logger.error(error_message)
            update_session(user_session_id, {"status": "error", "message": error_message})
            return {"status": "error", "processed_content": None}
        
        return {"status": "success", "processed_content": processed_content, "user_session_id": user_session_id, "input_type": input_type, "input_value": input_value}

    def exec(self, prep_res: dict) -> dict:
        logger.info("FAQGenerationNode: Executing...")
        if prep_res.get("status") == "error" or not prep_res.get("processed_content"):
            return {"status": "error", "generated_faqs": []}

        processed_content = prep_res["processed_content"]
        user_session_id = prep_res["user_session_id"]
        
        logger.info(f"Generating {NUM_FAQS_TO_GENERATE} FAQs for session {user_session_id}...")
        generated_faqs = generate_faqs(processed_content, num_faqs=NUM_FAQS_TO_GENERATE)

        if generated_faqs:
            logger.info(f"Successfully generated {len(generated_faqs)} FAQs.")
            return {"status": "success", "generated_faqs": generated_faqs, "user_session_id": user_session_id}
        else:
            logger.error("Failed to generate FAQs.")
            return {"status": "error", "generated_faqs": [], "user_session_id": user_session_id}

    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        logger.info("FAQGenerationNode: Post-processing...")
        user_session_id = exec_res.get("user_session_id")

        if exec_res.get("status") == "error":
            error_message = shared.get("error_message", "Failed to generate FAQs.")
            logger.error(f"FAQGenerationNode error for session {user_session_id}: {error_message}")
            update_session(user_session_id, {"status": "error", "message": error_message})
            return "error"

        generated_faqs = exec_res["generated_faqs"]
        shared["generated_faqs"] = generated_faqs

        logger.info("\n--- Generated FAQs ---")
        faq_content_for_embedding = []
        for i, faq in enumerate(generated_faqs):
            logger.info(f"  Q{i+1}: {faq['question']}")
            logger.info(f"  A{i+1}: {faq['answer']}")
            faq_content_for_embedding.append(f"Question: {faq['question']}\nAnswer: {faq['answer']}")
        logger.info("----------------------")

        # Embed and store FAQs for chat context
        if faq_content_for_embedding:
            logger.info("Embedding and storing FAQs for chat context...")
            
            original_input_type = shared.get("input_type")
            original_input_value = shared.get("input_value")

            combined_faq_text = "\n\n".join(faq_content_for_embedding)
            
            faq_embedded_chunk = {
                'text': combined_faq_text,
                'embedding': create_embedding(combined_faq_text),
                'source': original_input_value,
                'id': f"{user_session_id}-faq-combined-0"
            }
            
            if faq_embedded_chunk['embedding']:
                # --- CHANGE THIS FUNCTION CALL ---
                success = store_embeddings_in_qdrant([faq_embedded_chunk], original_input_type, user_session_id, source=original_input_value)
                # --- END CHANGE ---
                if success:
                    logger.info("FAQs successfully upserted to vector store for context.")
                    shared["context_is_ready"] = True
                else:
                    logger.error("Failed to upsert FAQs to vector store.")
            else:
                logger.error("Failed to create embedding for FAQs.")
        else:
            logger.warning("No FAQ content for embedding. Skipping FAQ embedding for chat context.")

        update_session(user_session_id, {"generated_faqs": generated_faqs, "status": "ready", "message": "FAQs generated and context updated."})
        logger.info(f"Saved {len(generated_faqs)} FAQs to session {user_session_id}.")

        logger.info("FAQGenerationNode: Post-processing complete.")
        return "default"