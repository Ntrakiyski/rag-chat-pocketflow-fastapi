from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, LLM_MODEL_DEFAULT


# Learn more about calling the LLM:
# https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(messages, model=None):
    """Call the LLM with the given messages and optional model."""
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    
    model_to_use = model or LLM_MODEL_DEFAULT
    print(f"Using model: {model_to_use}")
    
    try:
        # First validate model exists by listing available models
        available_models = client.models.list()
        if model_to_use not in [m.id for m in available_models.data]:
            raise ValueError(f"Invalid model specified: {model_to_use}")
            
        r = client.chat.completions.create(
            model=model_to_use,
            messages=messages
        )
        
        if (r.choices and 
                r.choices[0] and 
                r.choices[0].message and 
                r.choices[0].message.content is not None):
            return r.choices[0].message.content
            
        print("Warning: LLM returned no content.")
        return "I'm sorry, I couldn't generate a response at this time."
        
    except Exception as e:
        error_msg = str(e)
        if "Invalid model" in error_msg or "not found" in error_msg:
            raise ValueError(
                f"Invalid model specified: {model or LLM_MODEL_DEFAULT}"
            )
        raise


if __name__ == "__main__":
    test_messages = [
        {"role": "user", "content": "What is the meaning of life?"}
    ]
    print(call_llm(test_messages))
