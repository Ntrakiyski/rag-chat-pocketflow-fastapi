from openai import OpenAI
from app.core.config import OPENROUTER_API_KEY, WEB_SEARCH_MODEL_DEFAULT

def web_search(query: str) -> str:
    """
    Performs a web search using OpenRouter's perplexity/sonar-reasoning-pro model.

    Args:
        query (str): The search query.

    Returns:
        str: The search results as a string, or an empty string if an error occurs.
    """
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY is not set in config.py. Please set it in your .env file.")
        return ""

    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

        # The prompt for web search using a model like perplexity/sonar-reasoning-pro
        # is usually more direct, as the model is designed for search.
        # We'll ask it to provide a concise summary of search results.
        prompt = f"""Perform a web search for the following query and summarize the key findings:

Query: {query}
"""

        response = client.chat.completions.create(
            model=WEB_SEARCH_MODEL_DEFAULT,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error performing web search for query '{query}': {e}")
        return ""

if __name__ == "__main__":
    # Example usage
    search_query = "latest news on AI models"
    print(f"Performing web search for: {search_query}")
    results = web_search(search_query)
    if results:
        print("Search Results:")
        print(results)
    else:
        print("Failed to get web search results.")
