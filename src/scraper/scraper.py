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

        # 1. Discover sitemaps
        print("Step 1: Fetching sitemap index...")
        all_sitemap_urls = self.sitemap_processor.get_sitemap_urls_from_index(SITEMAP_INDEX_URL)
        if not all_sitemap_urls:
            print("Failed to fetch or parse sitemap index. Exiting.")
            return []
        print(f"Found {len(all_sitemap_urls)} total sitemaps listed in index.")

        relevant_sitemaps = self.sitemap_processor.filter_relevant_sitemaps(all_sitemap_urls)
        print(f"Found {len(relevant_sitemaps)} potentially relevant sitemaps (for sale/rent).")

        # 2. Discover and scrape search pages from relevant sitemaps
        all_properties = []
        pages_scraped_count = 0
        properties_found_count = 0 # Track properties found
        stop_scraping = False # Flag to break outer loop
        print("\nStep 2: Processing relevant sitemaps to find and scrape search result pages...")

        for sitemap_url in relevant_sitemaps:
            # Check limits before processing sitemap
            if pages_scraped_count >= self.max_search_pages:
                print(f"Reached limit of {self.max_search_pages} search pages. Stopping sitemap processing.")
                break
            if self.max_properties is not None and properties_found_count >= self.max_properties:
                print(f"Reached limit of {self.max_properties} properties. Stopping sitemap processing.")
                break # Already hit property limit

            page_urls_in_sitemap = self.sitemap_processor.get_page_urls_from_sitemap(sitemap_url)
            if not page_urls_in_sitemap:
                print(f"  No page URLs found or error processing sitemap: {sitemap_url}")
                continue # Skip if fetching/parsing failed or sitemap empty

            search_page_urls = self.sitemap_processor.filter_search_page_urls(page_urls_in_sitemap)
            print(f"  Found {len(search_page_urls)} potential search page URLs in {sitemap_url}")

            # Calculate how many more pages we can scrape based on page limit
            remaining_page_slots = max(0, self.max_search_pages - pages_scraped_count)
            urls_to_scrape_from_this_sitemap = search_page_urls[:remaining_page_slots]

            if not urls_to_scrape_from_this_sitemap:
                continue # No relevant URLs left to scrape within page limit

            print(f"  Attempting to scrape up to {len(urls_to_scrape_from_this_sitemap)} pages from this sitemap (respecting limits)...")
            for page_url in urls_to_scrape_from_this_sitemap:
                # Double check limits before fetching each page
                if pages_scraped_count >= self.max_search_pages:
                    stop_scraping = True # Signal outer loop to stop
                    break
                if self.max_properties is not None and properties_found_count >= self.max_properties:
                    stop_scraping = True # Signal outer loop to stop
                    break

                html = self.client.get(page_url, purpose="search page", delay=0.5)
                pages_scraped_count += 1 # Increment page count after attempting fetch
                if html:
                    extracted_properties = self.parser.parse(html)
                    if extracted_properties:
                        # Check if adding these properties exceeds the limit
                        properties_to_add = len(extracted_properties)
                        if self.max_properties is not None:
                            remaining_prop_slots = self.max_properties - properties_found_count
                            if properties_to_add > remaining_prop_slots:
                                print(f"    Limit reached: Adding only {remaining_prop_slots} of {properties_to_add} properties found on {page_url}")
                                extracted_properties = extracted_properties[:remaining_prop_slots]
                                properties_to_add = remaining_prop_slots # Update count to add
                                stop_scraping = True # Hit limit, ensure we stop after this page

                        print(f"    Extracted {properties_to_add} properties from {page_url}")
                        all_properties.extend(extracted_properties)
                        properties_found_count += properties_to_add

                    else:
                        print(f"    No properties extracted from {page_url}")

                else:
                    print(f"    Failed to fetch content for {page_url}")

                # Check property limit *after* processing page
                if self.max_properties is not None and properties_found_count >= self.max_properties:
                    stop_scraping = True
                    break # Stop processing pages in this sitemap

            if stop_scraping:
                break # Stop processing further sitemaps

        # 3. Report results
        print(f"\nStep 3: Scraping finished. Total pages scraped: {pages_scraped_count}. Total properties found: {properties_found_count}")
        return all_properties
