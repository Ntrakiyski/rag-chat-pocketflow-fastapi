from llama_cloud_services import LlamaParse
import os
import yaml
from dotenv import load_dotenv

load_dotenv() # Load environment variables

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text content from a PDF and returns it as a YAML formatted string.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: A YAML formatted string with the extracted text, or an empty string if an error occurs.
    """
    if not os.path.exists(file_path):
        print(f"Error: PDF file not found at {file_path}")
        return ""
    
    try:
        # Initialize LlamaParse with API key from environment variables
        # Ensure LLAMA_CLOUD_API_KEY is set in your .env file
        parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            result_type="text", # Using text for cleaner YAML output
        )

        # Parse the PDF file
        documents = parser.load_data(file_path)
        
        full_text = "\n\n".join([doc.text for doc in documents])

        # Create a dictionary to be converted to YAML
        yaml_output = {
            'source': file_path,
            'content': full_text
        }
        
        # Convert dictionary to YAML string
        return yaml.dump(yaml_output, sort_keys=False)

    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return ""

if __name__ == "__main__":
    # Example usage: Create a dummy PDF for testing or use an existing one
    # For a real test, you would need a PDF file.
    # Here's a placeholder for how you might test it:
    # dummy_pdf_path = "path/to/your/document.pdf"
    # if os.path.exists(dummy_pdf_path):
    #     print(f"Attempting to extract text from: {dummy_pdf_path}")
    #     text_content = extract_text_from_pdf(dummy_pdf_path)
    #     if text_content:
    #         print(f"Successfully extracted text. Length: {len(text_content)} characters.")
    #         print(text_content[:500]) # Print first 500 characters for a preview
    #     else:
    #         print("Failed to extract text from PDF.")
    # else:
    print("Please provide a valid PDF file path for testing in the __main__ block.")
