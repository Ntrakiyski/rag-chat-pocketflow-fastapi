import yaml
from firecrawl import FirecrawlApp, ScrapeOptions
from app.core.config import FIRECRAWL_API_KEY, MAX_CRAWL_PAGES

def crawl_website(url: str, max_pages: int = MAX_CRAWL_PAGES) -> str:
    """
    Fetches and processes content from a given website URL using Firecrawl and returns it as a YAML formatted string.
    This version correctly handles the response object from the Firecrawl SDK using dot notation.
    """
    if not FIRECRAWL_API_KEY:
        print("Error: FIRECRAWL_API_KEY is not set in config.py.")
        return ""

    try:
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        print(f"Starting synchronous crawl for URL: {url} with limit {max_pages}...")

        # This call returns a CrawlStatusResponse OBJECT.
        crawl_response = app.crawl_url(
            url,
            limit=max_pages,
            scrape_options=ScrapeOptions(onlyMainContent=True)
        )

        print(f"Crawl completed for URL: {url}.")

        # --- THIS IS THE FINAL FIX ---
        # 1. Check if the response object and its `.data` attribute exist.
        # 2. Access the `.data` attribute using dot notation.
        # 3. Access the `.markdown` attribute of each page object using dot notation.
        if crawl_response and hasattr(crawl_response, 'data') and crawl_response.data:
            
            # The result is a list of FirecrawlDocument objects.
            # We must use `page.markdown` (dot notation).
            full_content = "\n\n---\n\n".join(
                [page.markdown for page in crawl_response.data if hasattr(page, 'markdown') and page.markdown]
            )

            if not full_content:
                print(f"Crawl successful, but no markdown content found for URL: {url}")
                return ""

            yaml_output = {
                'source': url,
                'content': full_content
            }

            return yaml.dump(yaml_output, sort_keys=False)
        else:
            print(f"No content or data found in crawl response for URL: {url}")
            return ""
            
    except Exception as e:
        print(f"Error crawling website {url}: {e}")
        return ""


if __name__ == "__main__":
    # Example usage: Replace with a real URL for testing
    test_url = "https://www.firecrawl.dev/"
    print(f"Attempting to crawl: {test_url}")
    content = crawl_website(test_url)
    if content:
        print(f"Successfully crawled content. Length: {len(content)} characters.")
        # print(content[:500]) # Print first 500 characters for a preview
    else:
        print("Failed to crawl website.")
