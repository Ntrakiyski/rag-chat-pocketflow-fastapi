# filename: app/core/session.py

import redis
import json
import uuid
from app.core.config import SESSION_DB_URL, SESSION_DB_TOKEN
from app.schemas.models import SessionData
import ssl
from urllib.parse import urlparse, parse_qs # Ensure parse_qs is imported

def get_redis_client():
    parsed_url = urlparse(SESSION_DB_URL)
    
    # Determine if SSL is being used based on the URL scheme (rediss://)
    use_ssl = parsed_url.scheme == "rediss"

    # Start with common connection arguments
    connection_kwargs = {
        "decode_responses": True
    }

    if use_ssl:
        # If SSL is enabled, parse and add SSL-specific arguments
        query_params = parse_qs(parsed_url.query)
        
        # Get ssl_cert_reqs from URL query, default to CERT_REQUIRED if not specified
        cert_reqs_str = query_params.get('ssl_cert_reqs', ['required'])[0]
        ssl_cert_reqs_map = {
            'required': ssl.CERT_REQUIRED,
            'optional': ssl.CERT_OPTIONAL,
            'none': ssl.CERT_NONE
        }
        connection_kwargs['ssl_cert_reqs'] = ssl_cert_reqs_map.get(cert_reqs_str.lower(), ssl.CERT_REQUIRED)

        # Get ssl_check_hostname from URL query, default to True (or False if specified in URL)
        check_hostname_str = query_params.get('ssl_check_hostname', ['true'])[0]
        connection_kwargs['ssl_check_hostname'] = check_hostname_str.lower() == 'true'
        
    # Pass the dynamically built kwargs to redis.from_url
    return redis.from_url(
        SESSION_DB_URL,
        **connection_kwargs # Use double asterisk to unpack the dictionary as keyword arguments
    )

redis_client = get_redis_client()

def create_session(input_type: str, input_value: str) -> SessionData:
    session_id = str(uuid.uuid4())
    session_data = SessionData(
        user_session_id=session_id,
        input_type=input_type,
        input_value=input_value,
        active_namespaces=[]
    )
    redis_client.set(f"session:{session_id}", session_data.model_dump_json())
    return session_data

def get_session(session_id: str) -> SessionData | None:
    data = redis_client.get(f"session:{session_id}")
    if data:
        return SessionData.model_validate_json(data)
    return None

def update_session(session_id: str, updates: dict) -> SessionData | None:
    session_data = get_session(session_id)
    if session_data:
        updated_data = session_data.model_copy(update=updates)
        redis_client.set(f"session:{session_id}", updated_data.model_dump_json())
        return updated_data
    return None