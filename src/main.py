import sys
import os
from scraper.scraper import RightmoveScraper

# --- Main Execution Logic ---

def main():
    # You can adjust the number of pages to scrape here
    # Add a property limit for testing
    max_properties_to_scrape = 50
    scraper = RightmoveScraper(max_search_pages=5, max_properties=max_properties_to_scrape)
    all_properties = scraper.scrape()

    if all_properties:
        print(f"\nSuccessfully extracted data for {len(all_properties)} properties in total.")
        # Print the first 10 results as an example
        print("Showing first 10 results:")
        for i, prop in enumerate(all_properties[:10]):
            print(f"  Property {i+1}:")
            print(f"    Address: {prop.get('address', 'N/A')}") # Use .get for safety
            print(f"    Price: {prop.get('price', 'N/A')}") # Use .get for safety
        if len(all_properties) > 10:
            print("  ...")
    else:
        print("\nCould not extract any property data from the discovered search pages.")
        print("Possible reasons: Website structure changed, sitemap URLs outdated, or scraping was blocked.")

if __name__ == "__main__":
    main()
