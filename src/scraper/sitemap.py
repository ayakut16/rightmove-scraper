import xml.etree.ElementTree as ET
from io import StringIO

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

    def get_sitemap_urls_from_index(self, index_url):
        """Gets all sitemap URLs listed in a sitemap index file."""
        root = self._fetch_and_parse_sitemap(index_url)
        return self._get_locations_from_sitemap(root, 'sitemap')

    def get_page_urls_from_sitemap(self, sitemap_url):
        """Gets all page URLs listed in a specific sitemap file."""
        root = self._fetch_and_parse_sitemap(sitemap_url)
        return self._get_locations_from_sitemap(root, 'url')

    @staticmethod
    def filter_relevant_sitemaps(sitemap_urls):
        """Filters sitemap URLs for those likely containing property listings."""
        return [
            url for url in sitemap_urls
            if 'property-for-sale' in url or 'property-to-rent' in url
        ]

    @staticmethod
    def filter_search_page_urls(page_urls):
        """Filters page URLs for those matching the search result page pattern."""
        return [
            url for url in page_urls
            if ('/property-for-sale/' in url or '/property-to-rent/' in url) and \
               ('find.html' in url or '/find?' in url) and \
               ('locationIdentifier=' in url)
        ]
