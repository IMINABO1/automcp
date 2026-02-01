"""
Session utilities for loading cookies from session.json.
Works with any website by extracting domain from the request URL.
"""
import json
import os
from urllib.parse import urlparse

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session.json")


def get_request_cookies(url: str) -> dict:
    """
    Extract domain from URL and return matching cookies as a dict for httpx.

    Args:
        url: The full URL being requested (e.g., "https://trello.com/1/cards")

    Returns:
        Dict of cookie name -> value for the matching domain
    """
    domain = urlparse(url).netloc  # e.g., "trello.com"

    if not os.path.exists(SESSION_FILE):
        return {}

    with open(SESSION_FILE) as f:
        session = json.load(f)

    # Match cookies where the domain contains or is contained by the target
    # e.g., ".trello.com" matches "trello.com"
    cookies = {}
    for c in session.get('cookies', []):
        cookie_domain = c.get('domain', '')
        # Remove leading dot for comparison
        clean_cookie_domain = cookie_domain.lstrip('.')
        clean_target_domain = domain.lstrip('.')

        if clean_cookie_domain in clean_target_domain or clean_target_domain in clean_cookie_domain:
            cookies[c['name']] = c['value']

    return cookies


def get_csrf_token() -> str:
    """
    Get the dsc CSRF token for POST/PUT/DELETE requests.
    Required for write operations on sites like Trello.

    Returns:
        The CSRF token string, or empty string if not found
    """
    if not os.path.exists(SESSION_FILE):
        return ''

    with open(SESSION_FILE) as f:
        session = json.load(f)

    for c in session.get('cookies', []):
        if c['name'] == 'dsc':
            return c['value']

    return ''
