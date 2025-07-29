# filename: utils/qdrant_storage.py

from qdrant_client import QdrantClient, models
from app.core.config import QDRANT_HOST, QDRANT_API_KEY, EMBEDDING_MODEL_DIMENSION
from app.core.session import update_session, get_session
import traceback
import logging
from urllib.parse import urlparse
import os
import uuid # Keep uuid for generating point IDs

# --- REMOVED: HTTPS/Cloudflare specific imports ---
# import certifi 
# --------------------------------------------------

logger = logging.getLogger(__name__)


def get_qdrant_client():
    """
    Initializes and returns a new Qdrant client using the proven
    direct HTTP connection method to the server's IP.
    """
    logger.info(f"CELERY TASK: Connecting directly to Qdrant at {QDRANT_HOST}...")
    try:
        # --- SIMPLE, DIRECT CONNECTION ---
        # No 'verify' or 'headers' needed for direct HTTP connection.
        client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            timeout=60.0 # Keep a generous timeout
        )
        # ---------------------------------
        
        logger.info("Successfully created Qdrant client for task.")
        return client
    except Exception as e:
        logger.error(f"Failed to create Qdrant client for task: {e}", exc_info=True)
        return None


# Helper function to generate Qdrant-compatible collection names
def _generate_collection_name(input_type: str, source: str, user_session_id: str) -> str:
    session_prefix = user_session_id.split('-')[0]
    if input_type == "website":
        parsed_url = urlparse(source)
        domain = parsed_url.netloc.replace('.', '-').replace(':', '-')
        return f"web-{domain}-{session_prefix}".lower()
    elif input_type == "pdf":
        filename = os.path.basename(source).split('.')[0]
        filename = "".join(c if c.isalnum() else "-" for c in filename).strip("-")
        return f"pdf-{filename}-{session_prefix}".lower()
    else:
        return f"unknown-{session_prefix}".lower()


# Function to store embeddings in Qdrant
def store_embeddings_in_qdrant(embedded_chunks: list[dict], input_type: str, user_session_id: str, source: str = None):
    if not embedded_chunks:
        logger.warning("No embedded chunks to store.")
        return False

    qdrant_client = get_qdrant_client()

    if qdrant_client is None:
        logger.error("Failed to create Qdrant client for this task. Aborting.")
        return False

    try:
        vectors_to_upsert = []
        for i, chunk in enumerate(embedded_chunks):
            # The point ID MUST be a valid UUID.
            vector_id = str(uuid.uuid4())

            # Store all identifying info in the PAYLOAD.
            vector_payload = {
                "text": chunk['text'],
                "source": chunk['source'],
                "type": input_type,
                "session_id": user_session_id,
                "chunk_index": i
            }

            vectors_to_upsert.append(
                models.PointStruct(
                    id=vector_id,
                    vector=chunk['embedding'],
                    payload=vector_payload
                )
            )

        logger.info(f"Preparing to upsert {len(vectors_to_upsert)} vectors...")
        
        collection_name = _generate_collection_name(input_type, source, user_session_id)
        
        try:
            qdrant_client.get_collection(collection_name=collection_name)
            logger.info(f"Using existing collection '{collection_name}'.")
        except Exception:
            logger.info(f"Collection '{collection_name}' not found. Creating it now...")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_MODEL_DIMENSION,
                    distance=models.Distance.COSINE
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully.")

        qdrant_client.upsert(
            collection_name=collection_name,
            points=vectors_to_upsert,
            wait=True
        )
        
        logger.info(f"Successfully stored {len(vectors_to_upsert)} embedded chunks in Qdrant collection '{collection_name}'.")
        
        session_obj = get_session(user_session_id)
        if session_obj:
            current_namespaces = set(session_obj.active_namespaces)
            current_namespaces.add(collection_name)
            update_session(user_session_id, {'active_namespaces': list(current_namespaces)})
            logger.info(f"Session {user_session_id} updated with new collection: {collection_name}")
        else:
            logger.error(f"Failed to retrieve session {user_session_id} to update active_collections.")

        return True

    except Exception as e:
        logger.error(f"Error during Qdrant operation: {e}", exc_info=True)
        return False