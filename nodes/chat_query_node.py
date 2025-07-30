# filename: nodes/chat_query_node.py

import datetime
import logging  # Added for logging within the node

# Import utilities from your central 'utils' folder
from utils.rag_query_engine import query_content as query_vector_db
from utils.web_search import web_search
from utils.call_llm import call_llm

# Import PocketFlow Node
from pocketflow import Node

# Import new session management from app.core
from app.core.session import get_session, update_session  # Corrected imports


logger = logging.getLogger(__name__)  # Initialize logger for this node


class ChatQueryNode(Node):
    def prep(self, shared: dict):
        """
        Prepares for execution by gathering user input and relevant context from the shared store.
        """
        logger.info("ChatQueryNode: Preparing...")

        # The user_query is now passed directly in the shared dictionary by the API endpoint.
        user_query = shared.get("user_query")
        user_session_id = shared.get("user_session_id")

        if not user_query:
            logger.warning(
                f"ChatQueryNode: No user query found in shared data "
                f"for session {user_session_id}."
            )
            return (None, None, "exit", True)  # Treat as exit or error if no query

        # Load the most current session data from Redis
        session_obj = get_session(user_session_id)
        if not session_obj:
            logger.error(
                f"ChatQueryNode: Session {user_session_id} not found in Redis."
            )
            return (user_query, [], user_session_id, True)  # Proceed as contextless chat if session missing

        # Initialize chat_history from session_obj, ensuring it's a list
        chat_history = session_obj.chat_history if session_obj.chat_history is not None else []
        context_is_ready = session_obj.context_is_ready

        # Append the current user query to the chat history
        chat_history.append({
            "role": "user",
            "content": user_query,
            "timestamp": datetime.datetime.now().isoformat()
        })
        # Update the session with the new user message immediately
        update_session(user_session_id, {"chat_history": chat_history})

        # Determine if chat should be contextless
        contextless_chat = not context_is_ready

        logger.info(
            f"ChatQueryNode: Prepared for session "
            f"{user_session_id}. Context ready: "
            f"{context_is_ready}"
        )
        return (user_query, chat_history, user_session_id, contextless_chat)

    def exec(self, prep_res: tuple, shared: dict) -> tuple:
        """
        Executes the core logic: querying content or LLM, with automated fallback.
        """
        user_query, chat_history, user_session_id, contextless_chat = prep_res

        if user_query is None or user_query.lower() == 'exit':
            return (None, None, "exit")

        # Validate model first (if specified)
        if shared.get("model"):
            try:
                # Test model validity by making a dummy call
                call_llm(
                    [{"role": "system", "content": "test"}],
                    shared["model"]
                )
            except Exception as e:
                if "Invalid model" in str(e):
                    return (
                        f"Invalid model specified: {shared['model']}",
                        [],
                        "invalid_model"
                    )
                raise

        logger.info(
            f"🤖 Assistant is thinking for session {user_session_id}..."
        )
        answer = ""
        resources = []
        action = "default" # Default action is to continue chat

        if contextless_chat:
            logger.info("  Querying LLM directly (contextless chat)...")
            try:
                # Call LLM with the full chat history and optional model
                answer = call_llm(
                    chat_history,
                    model=shared.get("model")
                )
            except Exception as e:
                if "Invalid model" in str(e) or "not found" in str(e):
                    # This is a model validation error from OpenRouter
                    answer = f"Invalid model specified: {shared.get('model')}. Please check the model name. Available models can be found at https://openrouter.ai/models"
                    action = "invalid_model"
                    shared["error_message"] = answer  # Store detailed error for API response
                else:
                    answer = f"Error calling LLM: {e}"
                    action = "error"
                    shared["error_message"] = answer
                logger.error(f"Error in LLM call for session {user_session_id}: {e}", exc_info=True)
        else:
            logger.info("  Querying content from vector store...")
            try:
                # query_vector_db expects (query, user_session_id)
                answer, resources = query_vector_db(user_query, user_session_id)
            except Exception as e:
                logger.error(f"Error querying vector DB for session {user_session_id}: {e}", exc_info=True)
                answer = "" # Clear answer if there's an error in query_content

            # Automated fallback: If RAG fails or provides a non-answer, try web search.
            # "cannot answer" is a common LLM response when context is insufficient.
            if not answer or "cannot answer" in answer.lower() or "no relevant context" in answer.lower():
                logger.info("  No direct answer found in indexed content. Attempting web search...")
                try:
                    web_results = web_search(user_query)
                    if web_results:
                        answer = "(Web Search Result) " + web_results
                        resources.append({"source": "web_search", "text_snippet": web_results})
                        logger.info(f"  Web search successful for session {user_session_id}.")
                    else:
                        logger.info(f"  Web search yielded no results for session {user_session_id}. Falling back to general LLM chat.")
                        # Fallback to general LLM chat if web search fails
                        answer = call_llm(
                            chat_history,
                            model=shared.get("model")
                        )
                except Exception as e:
                    logger.error(f"Error during web search or fallback LLM call for session {user_session_id}: {e}", exc_info=True)
                    answer = f"I'm sorry, I encountered an error and couldn't find an answer."
                    action = "error"
            else:
                logger.info(f"  Answer found in vector store for session {user_session_id}.")

        logger.info(
            f"🤖 Assistant response for session {user_session_id}: "
            f"{answer[:100]}..."  # Log first 100 chars
        )
        return (answer, resources, action)

    def post(self, shared: dict, prep_res: tuple, exec_res: tuple) -> str:
        """
        Updates the shared state with the results of the execution and saves to Redis.
        """
        user_query, chat_history_from_prep, user_session_id, contextless_chat_from_prep = prep_res
        answer, resources, action = exec_res

        if action == "exit":
            logger.info(f"ChatQueryNode: Exiting session {user_session_id}.")
            return action
        
        if action == "error":
            shared["error_message"] = answer # Store the error message
            logger.error(f"ChatQueryNode: Error encountered for session {user_session_id}: {answer}")
            # Update session with error status
            update_session(user_session_id, {"status": "error", "message": answer})
            return action # Propagate error action

        # Append the assistant's response to the chat history
        if answer:
            chat_history_from_prep.append({
                "role": "assistant",
                "content": answer,
                "resources": resources,
                "timestamp": datetime.datetime.now().isoformat()
            })

        # Update the session in Redis using the new app.core.session module
        update_session(user_session_id, {
            "chat_history": chat_history_from_prep,
            "current_question": user_query,
            "current_answer": answer,
            "current_answer_resources": resources,
            "status": "ready" # Set status back to ready after a chat turn
        })
        logger.info(f"ChatQueryNode: Session {user_session_id} updated with assistant response.")

        return action # This will typically be "default" to allow continuous chat if API endpoint loops.
