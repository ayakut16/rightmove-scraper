from parsel import Selector
import json
from typing import Optional

class PropertyPageParser:
    def parse(self, html_content: str) -> Optional[dict]:
        """
        Parses property information from the provided HTML content.

        Args:
            html_content: A string containing the HTML of the property page.

        Returns:
            A dictionary containing the parsed property information,
            or None if the input is invalid.
        """
        if not html_content:
            return None

        try:
            selector = Selector(html_content)
            data = selector.xpath("//script[contains(.,'PAGE_MODEL = ')]/text()").get()

            if not data:
                return None

            json_data = next(self.find_json_objects(data))
            return json_data.get('propertyData')

        except Exception as e:
            print(f"Failed to parse property data: {e}")
            return None

    def find_json_objects(self, text: str, decoder=json.JSONDecoder()):
        """Find JSON objects in text, and generate decoded JSON data"""
        pos = 0
        while True:
            match = text.find("{", pos)
            if match == -1:
                break
            try:
                result, index = decoder.raw_decode(text[match:])
                yield result
                pos = match + index
            except ValueError:
                pos = match + 1
