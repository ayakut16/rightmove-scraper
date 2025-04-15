from .http_client import HttpClient
from .sitemap import SitemapProcessor
from .parser import SearchResultParser

SITEMAP_INDEX_URL = "https://www.rightmove.co.uk/sitemap.xml"

class RightmoveScraper:
    """Orchestrates the process of scraping Rightmove via sitemaps."""

    def __init__(self, max_search_pages=5, max_properties=None):
        """Initializes the scraper components."""
        self.client = HttpClient()
        self.sitemap_processor = SitemapProcessor(self.client)
        self.parser = SearchResultParser()
        self.max_search_pages = max_search_pages # Limit requests
        self.max_properties = max_properties # Limit total properties found

    def scrape(self):
        """Runs the full scraping process."""
        print("Starting scraper...")

        all_sitemap_urls = self._fetch_all_pages()
        if not all_sitemap_urls:
            return []

        # relevant_sitemaps = self._get_relevant_sitemaps(all_sitemap_urls)
        # return self._process_sitemaps(relevant_sitemaps)

    def _fetch_all_pages(self):
        """Fetches and processes the main sitemap index."""
        print("Step 1: Fetching all pages...")
        all_page_urls = self.sitemap_processor.get_all_page_urls_recursively(SITEMAP_INDEX_URL)
        if not all_page_urls:
            print("Failed to fetch or parse sitemap index. Exiting.")
            return None
        print(f"Found {len(all_page_urls)} total pages.")
        return all_page_urls

    def _get_relevant_sitemaps(self, all_sitemap_urls):
        """Filters sitemaps to find relevant ones."""
        relevant_sitemaps = self.sitemap_processor.filter_relevant_sitemaps(all_sitemap_urls)
        print(f"Found {len(relevant_sitemaps)} potentially relevant sitemaps (for sale/rent).")
        return relevant_sitemaps

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

    def _should_stop_processing(self, pages_scraped_count, properties_found_count):
        """Determines if scraping should stop based on limits."""
        if pages_scraped_count >= self.max_search_pages:
            print(f"Reached limit of {self.max_search_pages} search pages. Stopping sitemap processing.")
            return True
        if self.max_properties is not None and properties_found_count >= self.max_properties:
            print(f"Reached limit of {self.max_properties} properties. Stopping sitemap processing.")
            return True
        return False

    def _process_single_sitemap(self, sitemap_url, pages_scraped_count, properties_found_count):
        """Processes a single sitemap and returns extracted properties and counts."""
        page_urls = self._get_search_page_urls(sitemap_url)
        if not page_urls:
            return [], 0, 0

        remaining_pages = self.max_search_pages - pages_scraped_count
        urls_to_scrape = page_urls[:remaining_pages]

        if not urls_to_scrape:
            return [], 0, 0

        print(f"  Attempting to scrape up to {len(urls_to_scrape)} pages from this sitemap (respecting limits)...")
        return self._scrape_search_pages(urls_to_scrape, properties_found_count)

    def _get_search_page_urls(self, sitemap_url):
        """Extracts and filters search page URLs from a sitemap."""
        page_urls_in_sitemap = self.sitemap_processor.get_page_urls_from_sitemap(sitemap_url)
        if not page_urls_in_sitemap:
            print(f"  No page URLs found or error processing sitemap: {sitemap_url}")
            return []

        search_page_urls = self.sitemap_processor.filter_search_page_urls(page_urls_in_sitemap)
        print(f"  Found {len(search_page_urls)} potential search page URLs in {sitemap_url}")
        return search_page_urls

    def _scrape_search_pages(self, urls_to_scrape, properties_found_count):
        """Scrapes individual search pages and extracts properties."""
        all_properties = []
        pages_scraped = 0
        props_found = 0

        for page_url in urls_to_scrape:
            if self._should_stop_processing(pages_scraped, properties_found_count + props_found):
                break

            properties = self._scrape_single_page(page_url)
            if properties:
                properties_to_add = self._adjust_properties_for_limit(
                    properties,
                    properties_found_count + props_found
                )
                all_properties.extend(properties_to_add)
                props_found += len(properties_to_add)
            pages_scraped += 1

        return all_properties, pages_scraped, props_found

    def _scrape_single_page(self, page_url):
        """Scrapes a single search page and returns extracted properties."""
        html = self.client.get(page_url, purpose="search page", delay=0.5)
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
