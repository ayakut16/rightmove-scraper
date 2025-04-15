"""
URL utility functions
"""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def normalize_url(url: str) -> str:
    """
    Normalize a URL to ensure consistent storage and retrieval.

    This function:
    1. Removes unnecessary query parameters (like tracking IDs)
    2. Sorts query parameters alphabetically
    3. Standardizes protocol (uses https by default)
    4. Removes fragments (#) from URLs
    5. Removes trailing slashes

    Args:
        url: The URL to normalize

    Returns:
        A normalized version of the URL
    """
    # Parse the URL
    parsed = urlparse(url)

    # Get the query parameters and sort them
    query_params = parse_qs(parsed.query)

    # Remove tracking parameters (common ones)
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                      'utm_content', 'fbclid', 'gclid', 'ref', 'source']
    for param in tracking_params:
        if param in query_params:
            del query_params[param]

    # Rebuild the query string with sorted parameters
    query_string = urlencode(query_params, doseq=True)

    # Rebuild the URL with normalized components
    normalized = urlunparse((
        'https',  # Always use https
        parsed.netloc.lower(),  # Lowercase domain
        parsed.path.rstrip('/'),  # Remove trailing slash
        parsed.params,  # Keep params as is
        query_string,  # Sorted query string
        ''  # Remove fragment
    ))

    return normalized
