# Design Doc: Website & PDF Chat Application

> Please DON'T remove notes for AI

## Configuration Constants

- `NUM_FAQS_TO_GENERATE`: 5 (Default number of FAQs to generate)

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

This application aims to provide users with an intelligent chat interface to extract information and generate FAQs from both website content and uploaded PDF documents. The core problems it solves are:

1.  **Information Retrieval**: Users can quickly get answers to questions from large documents or websites without manual searching.
2.  **Content Summarization/Extraction**: Automatically generate a set number of FAQs from the provided content, offering a quick overview.
3.  **Versatility**: Support both web content (crawling) and local documents (PDFs).

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

1.  **RAG (Retrieval-Augmented Generation)**: For answering questions, the system will retrieve relevant chunks of information from the processed website/PDF content and then use an LLM to generate a coherent answer.
2.  **Workflow**: A sequential flow for processing user input, crawling/uploading, generating FAQs, and handling chat queries.

### Flow high-level Design:

1.  **Input Node**: User provides a website URL or uploads a PDF document.
2.  **Content Processing Node**: Based on input type, either crawls the website or extracts text from the PDF.
3.  **FAQ Generation Node (Optional)**: Generates a configurable number of FAQs from the processed content. This step can be skipped based on user preference.
4.  **Chat/Query Node**: User asks questions, and the system retrieves relevant information and generates answers, potentially looping for continuous interaction.

```mermaid
flowchart TD
    Input[User Input (URL/PDF)] --> ContentProcessing[Content Processing (Crawl/Extract)]
    ContentProcessing --> FAQGeneration{FAQ Generation?}
    FAQGeneration -- Yes --> GenerateFAQs[Generate FAQs]
    FAQGeneration -- No --> ChatQuery[Chat/Query Interface]
    GenerateFAQs --> ChatQuery
    ChatQuery --> Answer[Provide Answer]
```

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.
> 3. **Error Handling**: Each utility function should include robust error handling (e.g., try-except blocks, logging specific errors, returning error indicators or raising custom exceptions) to indicate success or failure and provide detailed error messages.

1.  **`call_llm`** (`utils/call_llm.py`)
    -   *Input*: `prompt` (str)
    -   *Output*: `response` (str)
    -   *Necessity*: Used by `generate_faqs` and `query_content` for LLM interactions.

2.  **`create_embedding`** (`utils/create_embedding.py`)
    -   *Input*: `text` (str)
    -   *Output*: `vector` (list of floats)
    -   *Necessity*: Used by LlamaIndex for generating embeddings for indexing and querying, specifically using OpenAI's small embedding model.

3.  **`crawl_website`** (`utils/firecrawl_utils.py`)
    -   *Input*: `url` (str)
    -   *Output*: `crawled_content` (str)
    -   *Necessity*: To fetch and process content from a given website URL using Firecrawl.

4.  **`generate_faqs`** (`utils/openrouter_faq_generator.py`)
    -   *Input*: `content` (str), `num_faqs` (int)
    -   *Output*: `faqs` (list of dicts, e.g., `[{"question": "...", "answer": "..."}]`)
    -   *Necessity*: To generate a specified number of FAQs from text using OpenRouter.

5.  **`extract_text_from_pdf`** (`utils/llamaindex_pdf_extractor.py`)
    -   *Input*: `file_path` (str)
    -   *Output*: `text_content` (str)
    -   *Necessity*: To extract raw text content from a PDF document using LlamaIndex's PDF reader capabilities.

6.  **`store_embeddings_in_redis`** (`utils/upstash_vector_storage.py`)
    -   *Input*: `documents` (list of dicts, each with 'id', 'text', 'metadata')
    -   *Output*: `success` (bool)
    -   *Necessity*: To take processed documents, generate embeddings using `create_embedding`, and store them directly into the Upstash vector database. This function ensures the content is ready for retrieval.

7.  **`web_search`** (`utils/web_search.py`)
    -   *Input*: `query` (str)
    -   *Output*: `search_results` (str)
    -   *Necessity*: To perform web searches using OpenRouter's `perplexity/sonar-reasoning-pro` model for general knowledge or external information.

8.  **`manage_user_session`** (`utils/redis_session_manager.py`)
    -   *Input*: `user_session_id` (str), `action` (str: 'save' or 'load'), `data` (dict, optional)
    -   *Output*: `session_data` (dict, if 'load' action)
    -   *Necessity*: To save and load user-specific interaction data (like chat history) to/from Redis, using a dedicated keyspace.

9.  **`query_vector_db`** (`utils/rag_query_engine.py`)
    -   *Input*: `user_session_id` (str), `query` (str)
    -   *Output*: `answer` (str), `resources` (list of dicts, e.g., `[{'source': 'filename.pdf', 'page': 1, 'line_range': '10-20', 'text_snippet': '...'}]` or `[{'source': 'website_url', 'text_snippet': '...'}]`)
    -   *Necessity*: To answer user questions by querying the Upstash vector database directly, retrieving relevant information based on the user's query and session context. It uses `create_embedding` to embed the query and then performs a similarity search.

### PocketFlow Flow Mechanics

In PocketFlow, a `Flow` orchestrates a collection of `Nodes`, defining the execution path through your workflow. It's the overall instruction set that tells the system the sequence of steps and what to do next based on the outcome of a step.

-   **Connecting Nodes with Actions**: Nodes are connected using the result of the previous Node's `post()` method, which returns an `Action` string. 
    -   The `>>` operator defines a default connection: `node_a >> node_b` means if `node_a.post()` returns "default" (or None), `node_b` runs next.
    -   Named action connections use `- "action" >>`: `node_a - "action_name" >> node_b` means if `node_a.post()` returns "action_name", `node_b` runs next.

-   **Creating and Running a Flow**: A `Flow` is created by specifying its `start` node (e.g., `my_flow = Flow(start=my_start_node)`). The entire workflow is executed by calling `flow.run(shared_data)`, which orchestrates the sequence of nodes based on their returned actions.

-   **Node.run() vs. Flow.run()**: `node.run(shared)` executes only that single node in isolation, useful for testing. `flow.run(shared)` executes the complete workflow pipeline by following the defined connections.

-   **Nested Flows**: A `Flow` can act as a `Node`, allowing for complex workflows to be broken down into smaller, reusable sub-flows. When a nested `Flow` is encountered, it executes its internal orchestration, and its `post()` method determines the next step in the parent `Flow`.

## Node Design

### Shared Store

> Notes for AI: Try to minimize data redundancy

The shared store structure will hold the state of the application, including user input, processed content, generated FAQs, and chat history.

```python
shared = {
    "input_type": "website" or "pdf",
    "input_value": "url" or "file_path",
    "processed_content": "string_of_all_text",

    "generated_faqs": [], # List of {'question': '...', 'answer': '...'}
    "web_search_results": "string", # Results from web_search utility
    "chat_history": [], # List of {'role': 'user'/'assistant', 'content': '...', 'timestamp': 'ISO_FORMAT_DATETIME'}
    "current_question": "string",
    "current_answer": "string",
    "current_answer_resources": [], # List of resources (metadata) for the current answer
    "user_session_id": "string", # Unique ID for the user's session
    "context_is_ready": False, # Flag to indicate if the vector DB is ready for querying
    "active_namespaces": [] # List of namespaces (e.g., user_session_id) where embeddings are stored

}
```

### Main Application Flow

The application will primarily consist of a single main flow that orchestrates the defined nodes. This flow will handle the end-to-end process from user input to providing chat responses and FAQs.

```python
# Assuming nodes are instantiated: input_node, content_processing_node, faq_generation_node, chat_query_node

# Define the main flow connections
input_node >> content_processing_node

# FAQ Generation is an optional branch
content_processing_node - "generate_faqs" >> faq_generation_node
content_processing_node - "skip_faqs" >> chat_query_node # If user opts out of FAQ generation

faq_generation_node >> chat_query_node

# The chat_query_node will likely loop internally for continuous interaction
# or transition to an 'end' state when the user exits.

main_app_flow = Flow(start=input_node)
```

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow.

1.  **InputNode**
    -   *Purpose*: Get the initial input from the user (URL or PDF file).
    -   *Type*: Regular
    -   *Steps*:
        -   *prep*: None
        -   *exec*: Prompt user for URL or file upload. Implement input validation to ensure valid URL or PDF file path. If input is invalid, report error.
        -   *post*: Store `input_type` and `input_value` in `shared`. Generate or retrieve `user_session_id` and store it in `shared`. Attempt to load existing session data using `manage_user_session`. If loading fails, log the error but proceed with a new session.

2.  **ContentProcessingNode**
    -   *Purpose*: Process the input (crawl website or extract text from PDF).
    -   *Type*: Regular (or Async if crawling is long-running)
    -   *Steps*:
        -   *prep*: Read `input_type` and `input_value` from `shared`.
        -   *exec*: If `input_type` is "website", attempt to call `crawl_website`. If `input_type` is "pdf", attempt to call `extract_text_from_pdf`. Implement try-except blocks to catch potential errors during crawling/extraction, log them, and set a flag indicating failure if an error occurs.
        -   *post*: If `exec` was successful, store `processed_content` in `shared`. Then, attempt to call `store_embeddings_in_redis` with the processed content. Catch and log any errors during storage. If `store_embeddings_in_redis` is successful, set `shared["context_is_ready"] = True` and add the `user_session_id` to `shared["active_namespaces"]`. If any step fails, ensure appropriate error messages are available in `shared` or logged.

3.  **FAQGenerationNode**
    -   *Purpose*: Generate FAQs from the processed content.
    -   *Type*: Regular
    -   *Steps*:
        -   *prep*: Read `processed_content` from `shared` and `NUM_FAQS_TO_GENERATE` constant. Check if `processed_content` is available and valid. If not, report error.
        -   *exec*: Attempt to call `generate_faqs`. Implement try-except blocks to catch potential errors during FAQ generation, log them, and set a flag indicating failure if an error occurs.
        -   *post*: If `exec` was successful, store `generated_faqs` in `shared`. If any step fails, ensure appropriate error messages are available in `shared` or logged.

4.  **ChatQueryNode**
    -   *Purpose*: Handle user questions and provide answers.
    -   *Type*: Regular
    -   *Steps*:
        -   *prep*: Read `chat_history`, `user_session_id`, and `context_is_ready` from `shared`. Check if `context_is_ready` is `True`. If not, report an error or handle the case where the vector DB is not ready for querying.
        -   *exec*: Get user query. If `context_is_ready` is `True`, attempt to call `query_vector_db` with `user_session_id` and the user query. The `query_vector_db` utility will return both the `answer` and `resources`. Implement robust error handling (try-except blocks, logging) to catch potential errors during query processing. Consider integrating `web_search` here if a relevant answer is not found in the indexed content, and handle potential errors from `web_search` as well. If `context_is_ready` is `False`, provide a default response indicating that the content is not yet processed.
        -   *post*: If `exec` was successful, store `current_question`, `current_answer`, `current_answer_resources`, and update `chat_history` in `shared`. Attempt to save updated `chat_history` and other relevant session data using `manage_user_session`. Catch and log any errors during session saving. If any step fails, ensure appropriate error messages are available in `shared` or logged.
