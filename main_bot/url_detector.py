import re
from typing import List, Tuple, Optional

# Regular expressions for detecting Terabox links
TERABOX_DOMAINS = [
    r'terabox\.com',
    r'teraboxapp\.com',
    r'1024tera\.com',
    r'4funbox\.com',
    r'mirrobox\.com',
    r'nephobox\.com',
    r'teraboxapp\.com',
    r'terabox\.app',
]

# Combine all domains into a single regex pattern
DOMAIN_PATTERN = '|'.join(TERABOX_DOMAINS)

# Full URL pattern with optional http/https and www
TERABOX_URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?(' + DOMAIN_PATTERN + r')(/[^\s]*)?',
    re.IGNORECASE
)

def extract_terabox_urls(text: str) -> List[str]:
    """Extract all Terabox URLs from a text message
    
    Args:
        text (str): The message text to analyze
        
    Returns:
        List[str]: List of extracted Terabox URLs
    """
    if not text:
        return []
    
    # Find all matches
    matches = TERABOX_URL_PATTERN.findall(text)
    
    # Reconstruct full URLs from matches
    urls = []
    for domain, path in matches:
        # Ensure path exists, default to root path
        path = path if path else '/'
        # Ensure URL has https:// prefix
        url = f"https://{domain}{path}"
        urls.append(url)
    
    return urls

def is_terabox_url(url: str) -> bool:
    """Check if a URL is a Terabox URL
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if it's a Terabox URL, False otherwise
    """
    return bool(TERABOX_URL_PATTERN.match(url))

def normalize_terabox_url(url: str) -> Optional[str]:
    """Normalize a Terabox URL to a standard format
    
    Args:
        url (str): URL to normalize
        
    Returns:
        Optional[str]: Normalized URL or None if not a Terabox URL
    """
    if not url:
        return None
    
    # Check if it's a Terabox URL
    match = TERABOX_URL_PATTERN.match(url)
    if not match:
        return None
    
    # Extract domain and path
    domain, path = match.groups()
    
    # Ensure path exists, default to root path
    path = path if path else '/'
    
    # Construct normalized URL
    normalized_url = f"https://{domain}{path}"
    
    return normalized_url