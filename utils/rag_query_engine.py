# filename: utils/rag_query_engine.py

from typing import List, Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse

from app.core.config import LLM_MODEL_DEFAULT, OPENAI_API_KEY, OPENROUTER_API_KEY
from app.core.session import get_session
from .qdrant_storage import get_qdrant_client # This correctly imports the working function

load_dotenv()
logger = logging.getLogger(__name__)


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


def query_content(query: str, user_session_id: str) -> tuple[str, list[dict]]:
    """
    Answers user questions by querying the indexed content in Qdrant.
    """
    # This correctly gets a fresh client for the task.
    qdrant_client = get_qdrant_client()
    
    if qdrant_client is None:
        logger.error("Failed to create Qdrant client for the query task. Cannot proceed.")
        return "Internal error: Vector DB connection failed.", []

    try:
        embedding_client = OpenAI(api_key=OPENAI_API_KEY)
        query_embedding = embedding_client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding

        session_data = get_session(user_session_id)
        active_collections = session_data.active_namespaces if session_data else []

        if not active_collections:
            logger.warning(f"No active collections found for session {user_session_id}. Cannot query.")
            return "I don't have any documents to search for this session. Please upload a PDF or provide a website first.", []

        all_query_results = []
        for collection_name in active_collections:
            logger.info(f"Querying collection: {collection_name}")
            try:
                qdrant_client.get_collection(collection_name=collection_name)
            except Exception:
                logger.warning(f"Collection '{collection_name}' not found for session {user_session_id}. Skipping.")
                continue

            search_result = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=3,
                with_payload=True,
            )
            all_query_results.extend(search_result)
        
        context_chunks = []
        resources = []
        all_query_results.sort(key=lambda x: x.score, reverse=True)
        
        for res in all_query_results:
            if res.payload and "text" in res.payload:
                context_chunks.append(res.payload["text"])
                resource_info: Dict[str, Any] = {
                    "text_snippet": res.payload["text"],
                    "source": res.payload.get("source", "unknown")
                }
                resources.append(resource_info)

        if not context_chunks:
            return "No relevant context was found in your documents to answer this question.", []

        context_str = "\n".join(context_chunks)
        prompt = f"Based on the following context, answer the question:\n\nContext:\n{context_str}\n\nQuestion: {query}\nAnswer:"

        chat_llm_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        answer = chat_llm_client.chat.completions.create(
            model=LLM_MODEL_DEFAULT,
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

        return answer, resources

    except Exception as e:
        logger.error(f"Error querying content: {e}", exc_info=True)
        return "An internal error occurred during content retrieval.", []