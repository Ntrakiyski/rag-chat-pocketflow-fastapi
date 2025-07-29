# **API Service Documentation: RAG Chat Application**

## 1. System Architecture

This document outlines the architecture for a scalable API service that provides intelligent chat capabilities over user-provided documents and websites. The system is designed for multi-user environments, ensuring a responsive user experience by decoupling immediate requests from long-running processes.

### 1.1. Architectural Pattern: API Server & Background Worker

The architecture is composed of two primary, independent components:

1.  **API Server (FastAPI):** A high-performance web server that serves as the main entry point for all client interactions. It handles authentication, request validation, and immediate responses. For time-consuming operations, it delegates work to the Background Worker.
2.  **Background Worker (Celery & Redis):** A dedicated process pool that executes computationally intensive tasks asynchronously. This includes content crawling, document parsing, text embedding, and feature enhancements like FAQ generation.

This separation ensures the API remains available and responsive, even under heavy processing load.

### 1.2. Data and Process Flow

The system supports two primary asynchronous workflows initiated by the user: initial content ingestion and on-demand FAQ generation.

```mermaid
flowchart TD
    subgraph "Client Application"
        A[1. POST /ingest] --> B{API Server (FastAPI)};
        B --> C[2. Returns {session_id, status: 'processing'}];
        D[3. GET /ingest/status/{session_id}] --> B;
        B --> E[4. Returns {status: 'ready'}];
        
        F[5. POST /chat/{session_id}] --> B;
        B --> G[6. Returns {answer: '...'}];

        H[7. POST /faq/generate/{session_id}] --> B;
        B --> I[8. Returns {status: 'faq_processing'}];
    end

    subgraph "Backend Infrastructure"
        B -- "Adds Ingestion Job" --> J((Task Queue - Redis));
        B -- "Adds FAQ Gen. Job" --> J;

        K[Background Worker (Celery)] -- "Picks up Job" --> J;
        K -- "Runs Ingestion or FAQ Flow" --> L[PocketFlow Engine];
        L -- "Uses" --> M[Nodes & Utils];
        M -- "Interacts with" --> N[External Services: Upstash, OpenAI, etc.];
    end
```

### 1.3. API Abstraction and Internal Workflows

A core design principle of this architecture is the separation of the public API from the internal business logic. The API exposes high-level, goal-oriented endpoints for the client (e.g., "ingest this document," "generate FAQs for this session").

The complex, multi-step processes required to fulfill these requests—such as text chunking, **embedding, vector storage, and retrieval**—are encapsulated within the **PocketFlow Engine**. These internal workflows **are not exposed as individual API endpoints**. Instead, they are triggered by the high-level API calls.

*   **Ingestion Workflow (Embedding & Upserting):**
    *   **Trigger:** A client sends a request to the `POST /ingest` endpoint.
    *   **Execution:** The API server places a single `run_ingestion_flow` job onto the task queue. The Background Worker picks up this job and executes the `setup_flow`. Within this flow, the `ContentProcessingNode` orchestrates the calls to the embedding and vector storage utilities.

*   **FAQ Generation Workflow:**
    *   **Trigger:** A client sends a request to the `POST /faq/generate/{session_id}` endpoint for an already ingested session.
    *   **Execution:** The API server places a `run_faq_generation_flow` job onto the task queue. The Background Worker executes a separate, dedicated flow that starts with the `FAQGenerationNode`, which generates, embeds, and upserts the new FAQ content into the existing session's vector store namespace.

*   **Chat Workflow (Retrieval & Generation):**
    *   **Trigger:** A client sends a request to the `POST /chat/{session_id}` endpoint.
    *   **Execution:** The API server directly invokes the `ChatQueryNode`. This node's internal logic handles the retrieval of relevant context from the vector store to generate a final answer.

## 2. API Endpoint Specification

All endpoints are versioned and prefixed with `/api/v1`.

### 2.1. Domain: Ingestion

Handles the initial processing of new content sources.

---

#### `POST /ingest`

*   **Description:** Initiates the asynchronous ingestion of new content. The server immediately returns a `session_id` for tracking the background job.
*   **Request (for Website):** `Content-Type: application/json`, Body: `{"input_type": "website", "input_value": "..."}`
*   **Request (for PDF):** `Content-Type: multipart/form-data`, Form Fields: `input_type`: "pdf", `file`: (file data)
*   **Success Response (202 Accepted):**
    ```json
    {
      "session_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
      "status": "processing",
      "message": "Content ingestion has started. Use the status endpoint to check for completion."
    }
    ```

---

#### `GET /ingest/status/{session_id}`

*   **Description:** Polls for the status of a specific content ingestion job.
*   **Request Parameters:** `session_id` (string, path parameter).
*   **Success Response (200 OK):**
    ```json
    {
      "session_id": "...",
      "status": "ready",
      "message": "Content is ready for chat."
    }
    ```
    *   **Note:** The `status` field can be one of `processing`, `ready`, or `error`.

---

### 2.2. Domain: Chat

Handles the interactive chat functionality.

---

#### `POST /chat/{session_id}`

*   **Description:** Submits a question to an active session and receives a context-aware answer. Requires ingestion status to be `ready`.
*   **Request Parameters:** `session_id` (string, path parameter).
*   **Request Body:** `{"question": "..."}`
*   **Success Response (200 OK):**
    ```json
    {
      "answer": "...",
      "resources": [...]
    }
    ```

---

### 2.3. Domain: FAQ Generation

Handles the on-demand creation and indexing of FAQs for an existing session.

---

#### `POST /faq/generate/{session_id}`

*   **Description:** Initiates an asynchronous job to generate FAQs for an already ingested session. This enhances the session's context for future chat queries.
*   **Request Parameters:** `session_id` (string, path parameter).
*   **Success Response (202 Accepted):**
    ```json
    {
      "session_id": "...",
      "status": "faq_processing",
      "message": "FAQ generation has started."
    }
    ```

---

### 2.4. Domain: Session Management

Provides endpoints for direct interaction with session data.

---

#### `GET /session/{session_id}`

*   **Description:** Retrieves the complete data object for a given session.
*   **Request Parameters:** `session_id` (string, path parameter).
*   **Success Response (200 OK):** A JSON object representing the full session state, including `chat_history`, `generated_faqs`, etc.

---

#### `PUT /session/{session_id}`

*   **Description:** Updates a session object with the provided data.
*   **Request Parameters:** `session_id` (string, path parameter).
*   **Request Body:** A JSON object representing the session fields to update.
*   **Success Response (200 OK):** `{"message": "Session updated successfully."}`

## 3. Implementation Plan

### Phase 1: Project Setup & Structure

1.  **Initialize Project Structure:** Reorganize the codebase into the `app/`, `nodes/`, and `utils/` directories.
2.  **Define Dependencies:** Update `requirements.txt` to include `fastapi`, `uvicorn[standard]`, `celery`, `redis`, `python-dotenv`, and `python-multipart`.
3.  **Centralize Configuration:** Create `app/core/config.py` to manage all settings.
4.  **Define Data Schemas:** Create `app/schemas/chat.py` to define all Pydantic models.

### Phase 2: Background Worker Implementation

1.  **Configure Celery:** Create `app/workers/celery_app.py` to define the Celery application instance.
2.  **Isolate Flow Logic:** Create `app/flows.py` to house the PocketFlow `Flow` definitions. This will include a `create_setup_flow` and a separate `create_faq_flow`.
3.  **Implement Worker Tasks:** Create `app/workers/tasks.py` to define two Celery tasks: `run_ingestion_flow` and `run_faq_generation_flow`.

### Phase 3: API Endpoint Implementation

1.  **Implement Ingestion Endpoints:** Create `app/api/endpoints/ingest.py`.
2.  **Implement Chat Endpoint:** Create `app/api/endpoints/chat.py`.
3.  **Implement FAQ Endpoint:** Create `app/api/endpoints/faq.py` to define the `POST /faq/generate/{session_id}` route.
4.  **Implement Session Endpoints:** Create `app/api/endpoints/session.py`.
5.  **Refactor Nodes for API:** Modify `ContentProcessingNode` to remove the interactive FAQ prompt and always return a `"default"` action. The `ChatQueryNode`'s web search prompt will be made non-interactive (e.g., automatically search if the initial RAG result is poor).

### Phase 4: Assembly and Verification

1.  **Assemble API Server:** Create `app/main.py` to initialize the FastAPI application and include all endpoint routers.
2.  **Create Run Script:** Develop a `run.sh` script to concurrently start the Celery worker and the Uvicorn API server.
3.  **End-to-End Testing:** Conduct comprehensive testing of all workflows:
    *   Test ingestion (URL and PDF).
    *   Test status polling.
    *   Test chat functionality.
    *   Test on-demand FAQ generation and verify that subsequent chat queries can leverage the new context.