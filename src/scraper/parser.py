from bs4 import BeautifulSoup
import json

class SearchResultParser:
    """Parses Rightmove search result pages to extract property data."""

    def parse(self, html_content):
        """Parses the HTML content and returns a list of property dicts."""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        properties = []

        # 1. Attempt to parse embedded JSON data (window.jsonModel)
        properties = self._parse_json_model(soup)

        # 2. If JSON parsing fails or returns no results, fall back to HTML scraping
        if not properties:
            properties = self._parse_html_elements(soup)

        return properties

    def _parse_json_model(self, soup):
        """Attempts to extract property data from the embedded window.jsonModel."""
        properties = []
        script_tag = soup.find('script', string=lambda t: t and 'window.jsonModel' in t)
        if not script_tag:
            return properties # No script tag found

        try:
            # Extract JSON string carefully
            json_str = script_tag.string.split('window.jsonModel = ', 1)[1].split(';')[0]
            data = json.loads(json_str)

            # Navigate the JSON structure (adjust path if needed)
            found_properties = data.get('properties', [])
            if not found_properties:
                print("Warning: 'properties' key not found or empty in window.jsonModel.")
                return properties

            # Extract details for each property
            for prop in found_properties:
                price_info = prop.get('price', {})
                # Handle potential variations in price display structure
                display_prices = price_info.get('displayPrices', [])
                price_display = 'N/A'
                if display_prices and isinstance(display_prices, list) and len(display_prices) > 0:
                    price_display = display_prices[0].get('displayPrice', 'N/A')

                address = prop.get('displayAddress', 'N/A')

                # Basic validation or placeholder logic
                if address != 'N/A' or price_display != 'N/A':
                    properties.append({
                        'address': address,
                        'price': price_display
                        # Add more fields here later if needed (e.g., URL, description)
                    })

        except (IndexError, TypeError, json.JSONDecodeError, AttributeError, KeyError) as e:
            print(f"Warning: Error parsing JSON data from script tag: {e}. Will attempt HTML fallback.")
            return [] # Return empty list to trigger fallback

        return properties

    def _parse_html_elements(self, soup):
        """Scrapes property data directly from HTML elements as a fallback."""
        properties = []
        # Common container classes (adjust if needed based on inspection)
        property_cards = soup.find_all('div', class_=lambda x: x and 'l-searchResult' in x.split()) # Main results
        if not property_cards:
            property_cards = soup.find_all('div', class_='propertyCard') # Older/alternate class
        if not property_cards:
             # Add other potential container selectors if necessary
             pass

        # print(f"Found {len(property_cards)} potential property card elements via HTML fallback.") # Debugging

        for card in property_cards:
            price = "N/A"
            address = "N/A"

            # Find price
            price_element = card.find('span', class_='propertyCard-priceValue')
            if not price_element:
                price_element = card.find('div', class_='property-card-price__price') # Another common selector
            # Add more price selectors if observed

            if price_element:
                price = price_element.get_text(strip=True)

            # Find address
            # Option 1: Specific address tag
            address_element = card.find('address', class_='propertyCard-address')
            # Option 2: Meta tag with itemprop (often more reliable)
            meta_address = card.find('meta', itemprop='streetAddress')

            if meta_address:
                address = meta_address.get('content', 'N/A')
            elif address_element:
                # Attempt to reconstruct address from parts within the tag
                address_parts = address_element.find_all(['span', 'meta'])
                if address_parts:
                    addr_texts = [part.get_text(strip=True) or part.get('content', '') for part in address_parts]
                    address = ', '.join(filter(None, addr_texts))
                else:
                    # Fallback to grabbing all text if specific parts aren't found
                    address = address_element.get_text(strip=True, separator=', ')
            # Add other address selectors if needed

            # Add property if we found *something*
            if address != 'N/A' or price != 'N/A':
                properties.append({
                    'address': address,
                    'price': price
                    # Add more fields here later
                })

        return properties
