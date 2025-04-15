import requests
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class HttpClient:
    """Handles HTTP requests with appropriate headers and delays."""
    def __init__(self, base_headers=None, default_timeout=15):
        self.headers = base_headers if base_headers is not None else HEADERS
        self.timeout = default_timeout

    def get(self, url, purpose="page", delay=0.5):
        """Performs a GET request."""
        print(f"Fetching {purpose}: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() # Check for HTTP errors
            if delay > 0:
                # print(f"Waiting for {delay} seconds...") # Optional: for debugging
                time.sleep(delay)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {purpose} {url}: {e}")
            return None
