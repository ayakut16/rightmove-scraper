import re

import xml.etree.ElementTree as ET
from io import StringIO
from tqdm import tqdm

from .fetcher import Fetcher

class SitemapProcessor:
    """Handles fetching, parsing, and extracting URLs from sitemaps."""

    def __init__(self):
        """Initializes with an Fetcher instance."""
        self.fetcher = Fetcher(cache_ttl_hours=1.0)

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

    async def   _fetch_and_parse_sitemap(self, url):
        """Fetches and parses a single sitemap (index or regular)."""
        xml_content = await self.fetcher.fetch_sitemap(url)
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

    async def get_all_page_urls(self, sitemap_root_url, outcodes=None):
        """
        Fetches and parses sitemaps starting from sitemap_seed_url,
        extracting all final page URLs (from <url> tags).
        Shows progress with tqdm progress bars.
        """
        all_page_urls = set()

        print(f"Fetching root sitemap: {sitemap_root_url}")
        root = await self._fetch_and_parse_sitemap(sitemap_root_url)
        child_sitemaps = self._get_locations_from_sitemap(root, 'sitemap')
        child_sitemaps = [sitemap for sitemap in child_sitemaps\
                           if outcodes is None or\
                            any(self._sitemap_contains_outcode(sitemap, outcode) for outcode in outcodes)]

        # Create progress bar for processing sitemaps
        with tqdm(total=len(child_sitemaps), desc="Processing sitemaps") as pbar:
            for sitemap_url in child_sitemaps:
                tqdm.write(f"Processing sitemap: {sitemap_url}")
                sitemap_content = await self._fetch_and_parse_sitemap(sitemap_url)
                page_url_locs = self._get_locations_from_sitemap(sitemap_content, 'url')
                all_page_urls.update(page_url_locs)
                pbar.update(1)

        return list(all_page_urls)

    def _sitemap_contains_outcode(self, sitemap_url, outcode):
        return re.search(fr'/sitemap-properties-{outcode}\d*\.xml$', sitemap_url) is not None
