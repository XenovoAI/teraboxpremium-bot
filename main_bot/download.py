import requests
import json
import time
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

# Rate limiting settings
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

class TeraboxDownloader:
    """Class to handle Terabox download processing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_share_id(self, url: str) -> Optional[str]:
        """Extract share ID from Terabox URL
        
        Args:
            url (str): Terabox URL
            
        Returns:
            Optional[str]: Share ID or None if not found
        """
        try:
            # Parse URL
            parsed_url = urlparse(url)
            
            # Extract from path
            path_match = re.search(r'/s/([\w-]+)', parsed_url.path)
            if path_match:
                return path_match.group(1)
            
            # Extract from query parameters
            query_params = parse_qs(parsed_url.query)
            if 'surl' in query_params:
                return query_params['surl'][0]
            
            return None
        except Exception as e:
            print(f"Error extracting share ID: {e}")
            return None
    
    def get_file_info(self, share_id: str) -> Tuple[bool, Dict]:
        """Get file information from Terabox
        
        Args:
            share_id (str): Terabox share ID
            
        Returns:
            Tuple[bool, Dict]: (Success status, File info or error message)
        """
        try:
            # Construct API URL
            api_url = f"https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl={share_id}"
            
            # Make request with retries
            response = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.session.get(api_url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)  # Wait before retrying
                    else:
                        raise
            
            if not response or response.status_code != 200:
                return False, {"error": "Failed to get file information"}
            
            # Parse response
            data = response.json()
            
            if not data.get('ok', False):
                return False, {"error": data.get('msg', 'Unknown error')}
            
            return True, data
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_download_link(self, share_id: str) -> Tuple[bool, Dict]:
        """Get direct download link for Terabox file
        
        Args:
            share_id (str): Terabox share ID
            
        Returns:
            Tuple[bool, Dict]: (Success status, Download info or error message)
        """
        try:
            # First get file info
            success, file_info = self.get_file_info(share_id)
            if not success:
                return False, file_info
            
            # Construct download API URL
            api_url = f"https://terabox-dl.qtcloud.workers.dev/api/get-download?shorturl={share_id}"
            
            # Make request with retries
            response = None
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.session.get(api_url, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)  # Wait before retrying
                    else:
                        raise
            
            if not response or response.status_code != 200:
                return False, {"error": "Failed to get download link"}
            
            # Parse response
            data = response.json()
            
            if not data.get('ok', False):
                return False, {"error": data.get('msg', 'Unknown error')}
            
            # Combine file info with download link
            result = {
                "filename": file_info.get('info', {}).get('filename', 'Unknown'),
                "size": file_info.get('info', {}).get('size', 0),
                "download_url": data.get('download_url', ''),
                "is_folder": file_info.get('info', {}).get('is_dir', False),
                "share_id": share_id
            }
            
            return True, result
        except Exception as e:
            return False, {"error": str(e)}
    
    def process_url(self, url: str) -> Tuple[bool, Dict]:
        """Process Terabox URL to get download information
        
        Args:
            url (str): Terabox URL
            
        Returns:
            Tuple[bool, Dict]: (Success status, Download info or error message)
        """
        # Extract share ID
        share_id = self.extract_share_id(url)
        if not share_id:
            return False, {"error": "Invalid Terabox URL"}
        
        # Get download link
        return self.get_download_link(share_id)

# Create a singleton instance
downloader = TeraboxDownloader()

# Function to process a URL
def process_terabox_url(url: str) -> Tuple[bool, Dict]:
    """Process a Terabox URL to get download information
    
    Args:
        url (str): Terabox URL
        
    Returns:
        Tuple[bool, Dict]: (Success status, Download info or error message)
    """
    return downloader.process_url(url)