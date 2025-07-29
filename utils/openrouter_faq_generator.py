from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, LLM_MODEL_DEFAULT, NUM_FAQS_TO_GENERATE
import json

def generate_faqs(content: str, num_faqs: int = NUM_FAQS_TO_GENERATE) -> list[dict]:
    """
    Generates a specified number of FAQs from the given text content using OpenRouter.

    Args:
        content (str): The text content from which to generate FAQs.
        num_faqs (int): The number of FAQs to generate.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an FAQ
                    with 'question' and 'answer' keys. Returns an empty list if an error occurs.
    """
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY is not set in config.py. Please set it in your .env file.")
        return []

    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

        prompt = f"""Generate {num_faqs} frequently asked questions (FAQs) and their answers based on the following content. 
        Provide the output as a JSON array of objects, where each object has 'question' and 'answer' keys.

Content:
{content}

Example JSON format:
[
  {{"question": "What is the capital of France?", "answer": "The capital of France is Paris."}}
]
"""

        response = client.chat.completions.create(
            model=LLM_MODEL_DEFAULT, # Using the default LLM model for generation
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        response_content = response.choices[0].message.content
        faqs = json.loads(response_content)
        
        # Validate the structure of the generated FAQs
        if not isinstance(faqs, list):
            raise ValueError("Generated response is not a JSON array.")
        for faq in faqs:
            if not isinstance(faq, dict) or "question" not in faq or "answer" not in faq:
                raise ValueError("Each FAQ object must have 'question' and 'answer' keys.")
                
        return faqs

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from LLM: {e}")
        print(f"Raw response content: {response_content}")
        return []
    except Exception as e:
        print(f"Error generating FAQs: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    sample_content = """
    The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. 
    It is named after the engineer Gustave Eiffel, whose company designed and built the tower. 
    Constructed from 1887 to 1889 as the entrance to the 1889 World's Fair, it was initially 
    criticized by some of France's leading artists and intellectuals for its design, 
    but it has become a global cultural icon of France and one of the most recognisable structures in the world.
    """
    print("Generating FAQs...")
    generated_faqs = generate_faqs(sample_content, num_faqs=2)
    if generated_faqs:
        for i, faq in enumerate(generated_faqs):
            print(f"FAQ {i+1}:")
            print(f"  Q: {faq['question']}")
            print(f"  A: {faq['answer']}")
    else:
        print("Failed to generate FAQs.")
