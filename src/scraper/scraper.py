import re
from tqdm import tqdm

from .fetcher import Fetcher
from .sitemap import SitemapProcessor
from .parser import PropertyPageParser
from .constants import LONDON_OUTCODES
SITEMAP_URL = "https://www.rightmove.co.uk/sitemap.xml"

class RightmoveScraper:
    """Orchestrates the process of scraping Rightmove via sitemaps."""

    def __init__(self, london_only: bool = False):
        """Initializes the scraper components."""
        self.fetcher = Fetcher()
        self.sitemap_processor = SitemapProcessor()
        self.london_only = london_only

    async def scrape(self):
        """Runs the full scraping process."""
        print("Starting scraper...")

        all_page_urls = await self._fetch_all_pages_from_sitemap()
        all_property_urls_from_sitemap = [p for p in all_page_urls if "/properties/" in p]
        all_property_ids_from_sitemap = [re.search(r'/properties/(\d+)', url).group(1) for url in all_property_urls_from_sitemap]
        existing_property_ids = set(self.fetcher.get_existing_property_rightmove_ids())
        expired_property_ids = self.fetcher.get_expired_property_rightmove_ids()
        new_property_ids = [id for id in all_property_ids_from_sitemap if id not in existing_property_ids]
        print(f"Scraping {len(new_property_ids)} new properties and {len(expired_property_ids)} expired properties...")
        await self._scrape_all_properties(new_property_ids + expired_property_ids)
        await self.fetcher.close()

    async def _fetch_all_pages_from_sitemap(self):
        """Fetches and processes the main sitemap index."""
        print("Step 1: Fetching all pages from sitemap...")
        if self.london_only:
            all_page_urls = await self.sitemap_processor.get_all_page_urls(SITEMAP_URL, outcodes=LONDON_OUTCODES)
        else:
            all_page_urls = await self.sitemap_processor.get_all_page_urls(SITEMAP_URL)
        print(f"Found {len(all_page_urls)} total pages.")
        return all_page_urls

    async def _scrape_all_properties(self, property_ids):
        print(f"Scraping {len(property_ids)} properties...")

        chunk_size = 250
        with tqdm(total=len(property_ids), desc="Fetching properties") as pbar:
            for i in range(0, len(property_ids), chunk_size):
                chunk = property_ids[i:i + chunk_size]
                await self.fetcher.fetch_and_save_properties(chunk)
                pbar.update(len(chunk))

    async def _scrape_single_property_page(self, property_url):
        property = await self.fetcher.fetch_property(property_url)
        print(property)
