from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, LLM_MODEL_DEFAULT

# Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(messages):
    
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
    r = client.chat.completions.create(
        model=LLM_MODEL_DEFAULT,
        messages=messages
    )
    # Ensure content is not None before returning
    if r.choices and r.choices[0] and r.choices[0].message and r.choices[0].message.content is not None:
        return r.choices[0].message.content
    else:
        print("Warning: LLM returned no content.")
        return "I'm sorry, I couldn't generate a response at this time." # Return a default message
    
if __name__ == "__main__":
    test_messages = [{"role": "user", "content": "What is the meaning of life?"}]
    print(call_llm(test_messages)) 