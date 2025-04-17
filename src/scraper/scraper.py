import re
import asyncio
from tqdm import tqdm

from .fetcher import Fetcher
from .sitemap import SitemapProcessor
from .parser import SearchPageParser
from .constants import LONDON_OUTCODES
SITEMAP_URL = "https://www.rightmove.co.uk/sitemap.xml"

class RightmoveScraper:
    """Orchestrates the process of scraping Rightmove via sitemaps."""

    def __init__(self, london_only: bool = False):
        """Initializes the scraper components."""
        self.fetcher = Fetcher()
        self.sitemap_processor = SitemapProcessor()
        self.london_only = london_only
        self.search_page_parser = SearchPageParser()
    async def scrape(self):
        """Runs the full scraping process."""
        print("Starting scraper...")

        page_urls = await self._fetch_all_pages_from_sitemap()
        property_ids_from_sitemap = self._get_property_ids_from_sitemap(page_urls)
        property_ids_from_search_pages = await self._get_property_ids_from_search_pages(page_urls)

        existing_property_ids = set(self.fetcher.get_existing_property_rightmove_ids())
        expired_property_ids = self.fetcher.get_expired_property_rightmove_ids()

        new_property_ids_from_sitemap = [id for id in property_ids_from_sitemap if id not in existing_property_ids]
        new_property_ids_from_search_pages = [id for id in property_ids_from_search_pages if id not in existing_property_ids]

        all_property_ids = list(set(new_property_ids_from_sitemap + new_property_ids_from_search_pages + expired_property_ids))

        print(f"""
               Scraping
                {len(new_property_ids_from_sitemap)} new properties from sitemap
                {len(new_property_ids_from_search_pages)} new properties from search pages
                {len(expired_property_ids)} expired properties
                Total properties to scrape: {len(all_property_ids)}
               """)

        await self._scrape_all_properties(all_property_ids)
        await self.fetcher.close()

    def _get_property_ids_from_sitemap(self, page_urls):
        property_urls = [p for p in page_urls if "/properties/" in p]
        return [re.search(r'/properties/(\d+)', url).group(1) for url in property_urls]

    async def _get_property_ids_from_search_pages(self, page_urls):
        search_page_urls = [p for p in page_urls if "/property-for-sale/" in p or "/property-to-rent/" in p]
        print(f"Found {len(search_page_urls)} search pages to scrape")
        chunk_size = 80
        property_ids = []

        with tqdm(total=len(search_page_urls), desc="Fetching search pages") as pbar:
            for i in range(0, len(search_page_urls), chunk_size):
                chunk = search_page_urls[i:i + chunk_size]
                htmls = await asyncio.gather(*[self.fetcher.fetch_webpage(url) for url in chunk])
                for html in htmls:
                    property_ids.extend(self.search_page_parser.parse(html))
                pbar.update(len(chunk))

        return list(set(property_ids))

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

        chunk_size = 80
        with tqdm(total=len(property_ids), desc="Fetching properties") as pbar:
            for i in range(0, len(property_ids), chunk_size):
                chunk = property_ids[i:i + chunk_size]
                await self.fetcher.fetch_and_save_properties(chunk)
                pbar.update(len(chunk))

    async def _scrape_single_property_page(self, property_url):
        property = await self.fetcher.fetch_property(property_url)
        print(property)
