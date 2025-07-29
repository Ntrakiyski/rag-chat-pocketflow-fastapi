import yaml
from openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter
from app.core.config import OPENAI_API_KEY, EMBEDDING_MODEL_DEFAULT

def create_embedding(text: str) -> list[float]:
    """
    Generates an embedding for a single text chunk using OpenAI's embedding model.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL_DEFAULT
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating embedding for text chunk: {e}")
        return []

def process_and_embed_yaml(yaml_string: str, chunk_size: int = 600, chunk_overlap: int = 128) -> list[dict]:
    """
    Parses a YAML string, chunks the content, and generates embeddings for each chunk.

    Args:
        yaml_string (str): The YAML formatted string with 'source' and 'content'.
        chunk_size (int): The size of each text chunk.
        chunk_overlap (int): The overlap between consecutive chunks.

    Returns:
        list[dict]: A list of dictionaries, each containing the chunked text, its embedding, and the source.
    """
    try:
        data = yaml.safe_load(yaml_string)
        source = data.get('source', 'unknown')
        content = data.get('content', '')

        if not content:
            print("No content found in YAML to process.")
            return []

        # Initialize the text splitter
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(content)

        print(f"Split content from '{source}' into {len(chunks)} chunks.")

        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"Embedding chunk {i+1}/{len(chunks)}...")
            embedding = create_embedding(chunk)
            if embedding:
                embedded_chunks.append({
                    'source': source,
                    'text': chunk,
                    'embedding': embedding
                })
        
        return embedded_chunks

    except yaml.YAMLError as e:
        print(f"Error parsing YAML string: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during processing and embedding: {e}")
        return []

if __name__ == "__main__":
    # Example usage with a dummy YAML string
    dummy_yaml = """
    source: 'dummy_document.pdf'
    content: |
      This is the first sentence of a test document. It is used to demonstrate the chunking and embedding process.
      Here is a second sentence, which will likely be in the same chunk. The document continues with more text to ensure that chunking actually happens.
      This third sentence might start a new chunk depending on the chunk size. The process is designed to handle long documents by breaking them into smaller, manageable pieces.
      Each piece, or chunk, is then converted into a numerical representation called an embedding. This embedding captures the semantic meaning of the text.
    """
    
    print("Testing YAML processing and embedding...")
    embedded_data = process_and_embed_yaml(dummy_yaml)

    if embedded_data:
        print(f"\nSuccessfully created {len(embedded_data)} embedded chunks.")
        for i, item in enumerate(embedded_data):
            print(f"  Chunk {i+1}: Source='{item['source']}', Text='{item['text'][:50]}...', Embedding Length={len(item['embedding'])}")
    else:
        print("Failed to process and embed YAML content.")
