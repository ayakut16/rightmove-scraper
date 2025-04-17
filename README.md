# Rightmove Scraper

A powerful, efficient web scraper for extracting property listings from Rightmove, the UK's largest online real estate portal.

## Overview

This project provides a comprehensive solution for scraping property data from Rightmove's website. It uses sitemap-based discovery to find all property listings and efficiently downloads, parses, and stores property details for later analysis.

Key features:
- Sitemap-based property URL discovery
- Intelligent HTTP caching to minimize unnecessary requests
- Asynchronous processing for high performance
- Dual database support (PostgreSQL for production, SQLite for development)
- Robust error handling and retry mechanisms

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL (optional, for production use)
- uv (for package management and running)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rightmove-scraper.git
   cd rightmove-scraper
   ```

2. Create a virtual environment and activate it:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   uv pip install -e .
   ```

4. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```

   Then edit the `.env` file to include your PostgreSQL connection details (if using PostgreSQL).

## Usage

Run the scraper with:

```bash
uv run src/main
```

The scraper will:
1. Fetch Rightmove's sitemap
2. Extract all property URLs
3. Download property details
4. Parse and store the data in the configured database

## Project Structure

- `src/`: Main source code directory
  - `main.py`: Entry point for the application
  - `scraper/`: Core scraper package
    - `fetcher.py`: Handles HTTP requests with caching
    - `scraper.py`: Orchestrates the scraping process
    - `parser.py`: Parses HTML to extract property data
    - `sitemap.py`: Processes XML sitemaps to discover URLs
    - `http_client.py`: Low-level HTTP client with retry logic
    - `database/`: Database handling modules
      - `models.py`: Data models
      - `sqlite.py`: SQLite implementation
      - `postgres.py`: PostgreSQL implementation
    - `utils/`: Utility functions

## Database Configuration

The scraper supports two database backends:

1. **SQLite** (fallback option)
   - Used automatically if PostgreSQL URL is not configured
   - No configuration needed
   - Data stored in `content_cache.db`

2. **PostgreSQL** (recommended for production)
   - Set the `POSTGRES_URL` environment variable in your `.env` file:
     ```
     POSTGRES_URL=postgresql://<username>:<password>@localhost:5432/<database>
     ```
   - If the `POSTGRES_URL` cannot be found in your environment variables, the scraper will automatically fall back to using SQLite

## Performance Considerations

- The scraper uses asynchronous I/O for maximum throughput
- Content is cached to avoid redundant downloads
- Default cache TTL is 6 hours but can be configured

## Legal Disclaimer

This scraper is provided for educational purposes only. When using web scrapers, always:

1. Respect the website's `robots.txt` file
2. Implement reasonable rate limiting to avoid overloading servers
3. Check the website's Terms of Service to ensure compliance
4. Only use the data for personal/research purposes unless otherwise permitted

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
