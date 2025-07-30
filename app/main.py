# filename: app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # NEW IMPORT
from app.core.config import PROJECT_NAME, PROJECT_VERSION, PROJECT_DESCRIPTION, API_V1_STR
from app.api.endpoints import ingest, chat, faq, session

app = FastAPI(
    title=PROJECT_NAME,
    version=PROJECT_VERSION,
    description=PROJECT_DESCRIPTION,
    openapi_tags=[
        {"name": "Ingestion", "description": "Endpoints for content ingestion and status checks."},
        {"name": "Chat", "description": "Endpoints for interactive chat with ingested content."},
        {"name": "FAQ Generation", "description": "Endpoints for on-demand FAQ generation."},
        {"name": "Session Management", "description": "Endpoints for managing user sessions."},
    ]
)

# NEW: Add CORS Middleware
origins = [
    "http://localhost:3000",  # Allow your Next.js dev server
    "http://127.0.0.1:3000",  # Another common localhost variant
    "https://pocketflow-ui.worfklow.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include the routers from different modules
app.include_router(ingest.router, prefix=API_V1_STR, tags=["Ingestion"])
app.include_router(chat.router, prefix=API_V1_STR, tags=["Chat"])
app.include_router(faq.router, prefix=API_V1_STR, tags=["FAQ Generation"])
app.include_router(session.router, prefix=API_V1_STR, tags=["Session Management"])

@app.get("/", tags=["Root"])
async def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": f"Welcome to the {PROJECT_NAME}!"}