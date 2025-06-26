"""
URL utility functions for smart downloader.
"""

import re
import urllib.parse
from typing import Optional, Tuple, List
from urllib.parse import urlparse, urljoin, quote, unquote


class URLUtils:
    """Utility class for URL operations."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if a URL is valid and accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL by removing fragments and fixing encoding.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Remove fragment
            normalized = parsed._replace(fragment='')
            
            # Ensure proper encoding
            path = quote(unquote(parsed.path), safe='/')
            query = quote(unquote(parsed.query), safe='&=')
            
            normalized = normalized._replace(path=path, query=query)
            
            return normalized.geturl()
        except Exception:
            return url
    
    @staticmethod
    def join_url(base_url: str, relative_url: str) -> str:
        """
        Join base URL with relative URL safely.
        
        Args:
            base_url: Base URL
            relative_url: Relative URL to join
            
        Returns:
            Joined absolute URL
        """
        try:
            return urljoin(base_url, relative_url)
        except Exception:
            return relative_url
    
    @staticmethod
    def get_domain(url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        try:
            return urlparse(url).netloc
        except Exception:
            return ''
    
    @staticmethod
    def get_path(url: str) -> str:
        """
        Extract path from URL.
        
        Args:
            url: URL to extract path from
            
        Returns:
            URL path
        """
        try:
            return urlparse(url).path
        except Exception:
            return ''
    
    @staticmethod
    def get_filename_from_url(url: str) -> str:
        """
        Extract filename from URL.
        
        Args:
            url: URL to extract filename from
            
        Returns:
            Filename or empty string
        """
        try:
            path = urlparse(url).path
            filename = path.split('/')[-1]
            return unquote(filename) if filename else ''
        except Exception:
            return ''
    
    @staticmethod
    def get_file_extension(url: str) -> str:
        """
        Extract file extension from URL.
        
        Args:
            url: URL to extract extension from
            
        Returns:
            File extension (without dot) or empty string
        """
        try:
            filename = URLUtils.get_filename_from_url(url)
            if '.' in filename:
                return filename.split('.')[-1].lower()
            return ''
        except Exception:
            return ''
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same domain
        """
        try:
            domain1 = URLUtils.get_domain(url1)
            domain2 = URLUtils.get_domain(url2)
            return domain1 == domain2
        except Exception:
            return False
    
    @staticmethod
    def encode_url_path(path: str) -> str:
        """
        Encode URL path for safe transmission.
        
        Args:
            path: Path to encode
            
        Returns:
            Encoded path
        """
        try:
            return quote(path, safe='/')
        except Exception:
            return path
    
    @staticmethod
    def decode_url_path(path: str) -> str:
        """
        Decode URL path.
        
        Args:
            path: Path to decode
            
        Returns:
            Decoded path
        """
        try:
            return unquote(path)
        except Exception:
            return path
    
    @staticmethod
    def build_url(scheme: str, netloc: str, path: str = '', 
                  params: str = '', query: str = '', fragment: str = '') -> str:
        """
        Build URL from components.
        
        Args:
            scheme: URL scheme (http, https)
            netloc: Network location (domain:port)
            path: URL path
            params: URL parameters
            query: Query string
            fragment: Fragment identifier
            
        Returns:
            Complete URL
        """
        try:
            return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))
        except Exception:
            return ''
    
    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        """
        Extract URLs from text using regex.
        
        Args:
            text: Text to search for URLs
            
        Returns:
            List of found URLs
        """
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return url_pattern.findall(text)
    
    @staticmethod
    def get_url_depth(base_url: str, target_url: str) -> int:
        """
        Calculate the depth difference between two URLs.
        
        Args:
            base_url: Base URL
            target_url: Target URL
            
        Returns:
            Depth difference (0 = same level, positive = deeper)
        """
        try:
            base_path = URLUtils.get_path(base_url).rstrip('/')
            target_path = URLUtils.get_path(target_url).rstrip('/')
            
            base_parts = [p for p in base_path.split('/') if p]
            target_parts = [p for p in target_path.split('/') if p]
            
            return len(target_parts) - len(base_parts)
        except Exception:
            return 0
    
    @staticmethod
    def is_absolute_url(url: str) -> bool:
        """
        Check if URL is absolute (has scheme).
        
        Args:
            url: URL to check
            
        Returns:
            True if absolute URL
        """
        try:
            return bool(urlparse(url).scheme)
        except Exception:
            return False
    
    @staticmethod
    def get_parent_url(url: str) -> str:
        """
        Get parent directory URL.
        
        Args:
            url: URL to get parent of
            
        Returns:
            Parent URL
        """
        try:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if path_parts:
                path_parts.pop()  # Remove last part
                new_path = '/' + '/'.join(path_parts) + '/' if path_parts else '/'
            else:
                new_path = '/'
            
            return parsed._replace(path=new_path).geturl()
        except Exception:
            return url
    
    @staticmethod
    def clean_url(url: str) -> str:
        """
        Clean URL by removing unnecessary parts.
        
        Args:
            url: URL to clean
            
        Returns:
            Cleaned URL
        """
        try:
            # Remove common tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source'
            ]
            
            parsed = urlparse(url)
            if parsed.query:
                query_params = urllib.parse.parse_qs(parsed.query)
                clean_params = {k: v for k, v in query_params.items() 
                              if k not in tracking_params}
                clean_query = urllib.parse.urlencode(clean_params, doseq=True)
                parsed = parsed._replace(query=clean_query)
            
            return parsed.geturl()
        except Exception:
            return url 