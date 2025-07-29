from fastapi import FastAPI
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


app.include_router(ingest.router, prefix=API_V1_STR, tags=["Ingestion"])
app.include_router(chat.router, prefix=API_V1_STR, tags=["Chat"])
app.include_router(faq.router, prefix=API_V1_STR, tags=["FAQ Generation"])
app.include_router(session.router, prefix=API_V1_STR, tags=["Session Management"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to the {PROJECT_NAME}!"}
