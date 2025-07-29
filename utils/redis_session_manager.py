# filename: utils/redis_session_management.py

# --- FIX 1: Import from the correct library ---
from upstash_redis import Redis
import json
from datetime import datetime
from app.core.config import SESSION_DB_URL, SESSION_DB_TOKEN

REDIS_SESSION_PREFIX = "user_session:"

def manage_user_session(user_session_id: str, action: str, data: dict = None) -> dict or None:
    """
    Manages user-specific interaction data (like chat history) to/from Upstash
    using the official upstash-redis SDK.
    """
    if not user_session_id:
        print("Error: user_session_id cannot be empty.")
        return None

    try:
        # --- FIX 2: Initialize the Upstash Redis client ---
        # It's designed to work with the https:// URL and token.
        redis_client = Redis(url=SESSION_DB_URL, token=SESSION_DB_TOKEN)
    except Exception as e:
        print(f"Error connecting to Upstash Redis: {e}")
        return None

    session_key = f"{REDIS_SESSION_PREFIX}{user_session_id}"

    if action == 'save':
        if data is None:
            print("Error: Data must be provided for 'save' action.")
            return False # Return False for failure
        try:
            # The .set() method works similarly.
            # Load existing data to merge, especially for active_namespaces
            existing_data_json = redis_client.get(session_key)
            existing_data = json.loads(existing_data_json) if existing_data_json else {}

            # Merge new data with existing data
            # For chat_history, replace if provided
            if 'chat_history' in data: 
                existing_data['chat_history'] = data['chat_history']

            # For active_namespaces, add to a set to ensure uniqueness
            existing_namespaces = set(existing_data.get('active_namespaces', []))
            if 'active_namespaces' in data:
                existing_namespaces.update(data['active_namespaces'])
            existing_data['active_namespaces'] = list(existing_namespaces)

            redis_client.set(session_key, json.dumps(existing_data))
            print(f"Session {user_session_id} saved successfully via Upstash SDK.")
            return True
        except Exception as e:
            print(f"Error saving session {user_session_id}: {e}")
            return False
            
    elif action == 'load':
        try:
            # The .get() method works similarly.
            session_data_json = redis_client.get(session_key)
            if session_data_json:
                loaded_data = json.loads(session_data_json)
                # Ensure active_namespaces is a list if it exists
                if 'active_namespaces' in loaded_data and isinstance(loaded_data['active_namespaces'], list):
                    loaded_data['active_namespaces'] = list(set(loaded_data['active_namespaces'])) # Ensure uniqueness
                print(f"Session {user_session_id} loaded successfully via Upstash SDK.")
                return loaded_data
            else:
                print(f"No session data found for {user_session_id}.")
                return None
        except Exception as e:
            print(f"Error loading session {user_session_id}: {e}")
            return None
            
    else:
        print(f"Error: Invalid action '{action}'. Must be 'save' or 'load'.")
        return None

# The __main__ block for testing remains the same and should work with this new code.
if __name__ == "__main__":
    # ... (your existing __main__ block) ...
    pass