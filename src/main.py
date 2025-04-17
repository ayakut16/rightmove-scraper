import sys
import os
import asyncio
import json
from pprint import pprint
from scraper.fetcher import Fetcher
from scraper.scraper import RightmoveScraper

# --- Main Execution Logic ---

async def async_main():
    args = [arg.lower() for arg in sys.argv[1:]]
    scraper = RightmoveScraper(london_only=('--london' in args))
    await scraper.scrape()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
