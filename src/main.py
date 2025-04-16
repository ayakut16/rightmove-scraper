import sys
import os
import asyncio
import json
from pprint import pprint
from scraper.fetcher import Fetcher
from scraper.scraper import RightmoveScraper

# --- Main Execution Logic ---

async def async_main():
    scraper = RightmoveScraper()
    await scraper.scrape()

def main():
    print("Starting main function")
    asyncio.run(async_main())
    print("Main function completed")

if __name__ == "__main__":
    asyncio.run(main())
