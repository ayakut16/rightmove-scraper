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
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
