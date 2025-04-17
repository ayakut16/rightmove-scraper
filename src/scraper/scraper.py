from tqdm import tqdm

from .fetcher import Fetcher
from .sitemap import SitemapProcessor
from .parser import PropertyPageParser

SITEMAP_URL = "https://www.rightmove.co.uk/sitemap.xml"

class RightmoveScraper:
    """Orchestrates the process of scraping Rightmove via sitemaps."""

    def __init__(self):
        """Initializes the scraper components."""
        self.fetcher = Fetcher()
        self.sitemap_processor = SitemapProcessor()

    async def scrape(self):
        """Runs the full scraping process."""
        print("Starting scraper...")

        all_page_urls = await self._fetch_all_pages_from_sitemap()
        all_property_urls = [p for p in all_page_urls if "/properties/" in p]
        await self._scrape_all_properties(all_property_urls)
        await self.fetcher.close()

    async def _fetch_all_pages_from_sitemap(self):
        """Fetches and processes the main sitemap index."""
        print("Step 1: Fetching all pages from sitemap...")
        all_page_urls = await self.sitemap_processor.get_all_page_urls(SITEMAP_URL)
        print(f"Found {len(all_page_urls)} total pages.")
        return all_page_urls

    async def _scrape_all_properties(self, all_property_urls):
        print(f"Scraping {len(all_property_urls)} properties...")

        chunk_size = 250
        with tqdm(total=len(all_property_urls), desc="Fetching properties") as pbar:
            for i in range(0, len(all_property_urls), chunk_size):
                chunk = all_property_urls[i:i + chunk_size]
                await self.fetcher.fetch_and_save_properties(chunk)
                pbar.update(len(chunk))

    async def _scrape_single_property_page(self, property_url):
        property = await self.fetcher.fetch_property(property_url)
        print(property)
