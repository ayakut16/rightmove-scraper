import asyncio
import html
from typing import Optional
from httpx import AsyncClient, Response

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9,lt;q=0.8,et;q=0.7,de;q=0.6",
}

class HttpClient:
    """Handles async HTTP requests with appropriate headers."""
    def __init__(self, base_headers=None, default_timeout=30):
        self.client = AsyncClient(
            headers=base_headers if base_headers is not None else DEFAULT_HEADERS,
            follow_redirects=True,
            http2=True,  # enable http2 to reduce block chance
            timeout=default_timeout,
        )

    async def get(self, url: str, delay: float = 0.1) -> Optional[str]:
        """Performs an async GET request."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)

            response = await self.client.get(url)

            # Only raise for 4xx and 5xx status codes
            response.raise_for_status()

            return response.text, response.status_code
        except Exception as e:
            return None, e.response.status_code

    async def close(self):
        """Close the async client."""
        await self.client.aclose()
