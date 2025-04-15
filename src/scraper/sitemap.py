import xml.etree.ElementTree as ET
from io import StringIO
from collections import deque # Added for queue

class SitemapProcessor:
    """Handles fetching, parsing, and extracting URLs from sitemaps."""

    def __init__(self, http_client):
        """Initializes with an HttpClient instance."""
        self.client = http_client

    def _parse_xml_sitemap(self, xml_content):
        """Helper function to parse XML content, handling namespaces."""
        if not xml_content:
            return None
        try:
            it = ET.iterparse(StringIO(xml_content))
            for _, el in it:
                prefix, has_namespace, postfix = el.tag.partition('}')
                if has_namespace:
                    el.tag = postfix  # strip namespace
            return it.root
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return None

    def _fetch_and_parse_sitemap(self, url):
        """Fetches and parses a single sitemap (index or regular)."""
        # Use a longer delay for sitemaps
        xml_content = self.client.get(url, purpose="sitemap", delay=1.0)
        return self._parse_xml_sitemap(xml_content)

    def _get_locations_from_sitemap(self, root, element_name):
        """Extracts <loc> text content from sitemap elements."""
        locations = []
        if root is None:
            return locations
        for element in root.findall(element_name):
            loc_element = element.find('loc')
            if loc_element is not None and loc_element.text:
                locations.append(loc_element.text)
        return locations

    def get_all_page_urls_recursively(self, start_url, page_limit=10):
        """
        Recursively fetches and parses sitemaps starting from start_url,
        extracting all final page URLs (from <url> tags).
        """
        all_page_urls = set()
        sitemap_queue = deque([start_url])
        processed_sitemaps = set() # To avoid infinite loops

        while sitemap_queue:
            print(f"Queue size: {len(sitemap_queue)}")
            current_sitemap_url = sitemap_queue.popleft()
            if 'properties' not in current_sitemap_url and current_sitemap_url != start_url:
                continue
            if current_sitemap_url in processed_sitemaps:
                continue
            processed_sitemaps.add(current_sitemap_url)

            print(f"Processing sitemap: {current_sitemap_url}")
            root = self._fetch_and_parse_sitemap(current_sitemap_url)
            if root is None:
                print(f"  Skipping {current_sitemap_url} due to fetch/parse error.")
                continue

            # Check for nested sitemaps first (<sitemap>)
            nested_sitemap_locs = self._get_locations_from_sitemap(root, 'sitemap')
            if nested_sitemap_locs:
                print(f"  Found {len(nested_sitemap_locs)} nested sitemaps in {current_sitemap_url}")
                for loc in nested_sitemap_locs:
                    if loc not in processed_sitemaps:
                        sitemap_queue.append(loc)

            # If no <sitemap> tags, it's likely a sitemap with <url> tags
            page_url_locs = self._get_locations_from_sitemap(root, 'url')
            if page_url_locs:
                print(f"  Found {len(page_url_locs)} page URLs in {current_sitemap_url}")
                all_page_urls.update(page_url_locs)
            else:
                # Could be an index pointing to other indexes, or empty
                print(f"  No <sitemap> or <url> tags found in {current_sitemap_url}")

        return list(all_page_urls)
