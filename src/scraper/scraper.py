from .fetcher import Fetcher
from .sitemap import SitemapProcessor
from .parser import SearchResultParser

SITEMAP_URL = "https://www.rightmove.co.uk/sitemap.xml"

class RightmoveScraper:
    """Orchestrates the process of scraping Rightmove via sitemaps."""

    def __init__(self):
        """Initializes the scraper components."""
        self.fetcher = Fetcher()
        self.sitemap_processor = SitemapProcessor()
        self.parser = SearchResultParser()

    def scrape(self):
        """Runs the full scraping process."""
        print("Starting scraper...")

        all_page_urls = self._fetch_all_pages_from_sitemap()
        all_property_urls = [p for p in all_page_urls if "/properties/" in p]
        # for url in all_property_urls:
        #     properties = self._scrape_single_page(url)
        #     print(properties)

    def _fetch_all_pages_from_sitemap(self):
        """Fetches and processes the main sitemap index."""
        print("Step 1: Fetching all pages from sitemap...")
        all_page_urls = self.sitemap_processor.get_all_page_urls(SITEMAP_URL)
        print(f"Found {len(all_page_urls)} total pages.")
        return all_page_urls

    def _process_sitemaps(self, relevant_sitemaps):
        """Processes each relevant sitemap and extracts property data."""
        print("\nStep 2: Processing relevant sitemaps to find and scrape search result pages...")
        all_properties = []
        pages_scraped_count = 0
        properties_found_count = 0

        for sitemap_url in relevant_sitemaps:
            if self._should_stop_processing(pages_scraped_count, properties_found_count):
                break

            properties, pages_count, props_count = self._process_single_sitemap(
                sitemap_url,
                pages_scraped_count,
                properties_found_count
            )

            all_properties.extend(properties)
            pages_scraped_count += pages_count
            properties_found_count += props_count

        self._print_final_results(pages_scraped_count, properties_found_count)
        return all_properties

    def _scrape_single_page(self, page_url):
        """Scrapes a single search page and returns extracted properties."""
        html = self.fetcher.fetch(page_url)
        if not html:
            print(f"    Failed to fetch content for {page_url}")
            return []

        properties = self.parser.parse(html)
        if not properties:
            print(f"    No properties extracted from {page_url}")
            return []

        print(f"    Extracted {len(properties)} properties from {page_url}")
        return properties

    def _adjust_properties_for_limit(self, properties, current_count):
        """Adjusts the number of properties based on the maximum limit."""
        if self.max_properties is None:
            return properties

        remaining_slots = self.max_properties - current_count
        if remaining_slots <= 0:
            return []

        if len(properties) > remaining_slots:
            print(f"    Limit reached: Adding only {remaining_slots} of {len(properties)} properties")
            return properties[:remaining_slots]

        return properties

    def _print_final_results(self, pages_scraped_count, properties_found_count):
        """Prints the final scraping results."""
        print(f"\nStep 3: Scraping finished. Total pages scraped: {pages_scraped_count}. "
              f"Total properties found: {properties_found_count}")
