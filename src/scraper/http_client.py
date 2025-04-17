import asyncio
import html
from typing import Optional, Any
from httpx import AsyncClient, Response
import httpx

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

    async def get(self, url: str, delay: float = 0.1, max_retries: int = 5) -> tuple[Optional[str], Any]:
        """Performs an async GET request with retries."""
        for attempt in range(max_retries):
            try:
                if delay > 0:
                    await asyncio.sleep(delay)

                response = await self.client.get(url)

                if response.status_code == 404 or response.status_code == 410:
                    return None, response.status_code

                response.raise_for_status()
                return response.text, response.status_code

            except httpx.ReadError as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                # Close the existing client
                await self.client.aclose()

                # Create a new client with the same settings
                self.client = AsyncClient(
                    headers=self.client.headers,
                    follow_redirects=True,
                    http2=True,
                    timeout=self.client.timeout,
                )

                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def close(self):
        """Close the async client."""
        await self.client.aclose()
