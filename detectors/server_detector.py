"""
Server detection module for analyzing target servers.
"""

import requests
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse


@dataclass
class ServerInfo:
    """Server information data structure."""
    server_type: str
    page_structure: str
    estimated_files: int
    estimated_size: int
    supports_range: bool
    encoding: str
    response_time: float
    content_type: str


class ServerDetector:
    """Detects server type and capabilities."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartDownloader/1.0 (Compatible; Analysis Bot)'
        })
    
    def analyze_server(self, url: str) -> ServerInfo:
        """Analyze server and return comprehensive information."""
        # Get basic server info
        server_type, response_time = self._detect_server_type(url)
        supports_range = self._check_range_support(url)
        encoding = self._detect_encoding(url)
        
        # Analyze page structure
        page_structure, estimated_files, content_type = self._analyze_page_structure(url)
        
        # Estimate total size (placeholder for now)
        estimated_size = estimated_files * 1024 * 1024  # Rough estimate: 1MB per file
        
        return ServerInfo(
            server_type=server_type,
            page_structure=page_structure,
            estimated_files=estimated_files,
            estimated_size=estimated_size,
            supports_range=supports_range,
            encoding=encoding,
            response_time=response_time,
            content_type=content_type
        )
    
    def _detect_server_type(self, url: str) -> Tuple[str, float]:
        """Detect server type from HTTP headers."""
        try:
            import time
            start_time = time.time()
            response = self.session.head(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            server_header = response.headers.get('Server', '').lower()
            
            if 'apache' in server_header:
                return 'apache', response_time
            elif 'nginx' in server_header:
                return 'nginx', response_time
            elif 'simplehttp' in server_header or 'python' in server_header:
                return 'simplehttp', response_time
            elif 'iis' in server_header:
                return 'iis', response_time
            else:
                return 'unknown', response_time
                
        except Exception:
            return 'unknown', 0.0
    
    def _check_range_support(self, url: str) -> bool:
        """Check if server supports HTTP Range requests."""
        try:
            headers = {'Range': 'bytes=0-1'}
            response = self.session.head(url, headers=headers, timeout=self.timeout)
            return response.status_code == 206
        except Exception:
            return False
    
    def _detect_encoding(self, url: str) -> str:
        """Detect page encoding."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            return response.encoding or 'utf-8'
        except Exception:
            return 'utf-8'
    
    def _analyze_page_structure(self, url: str) -> Tuple[str, int, str]:
        """Analyze page structure and count links."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            content = response.text
            content_type = response.headers.get('Content-Type', '')
            
            # Check for directory listing patterns
            if self._is_directory_listing(content):
                link_count = self._count_directory_links(content)
                return 'directory_listing', link_count, content_type
            elif self._is_api_response(content, content_type):
                return 'api', 0, content_type
            else:
                link_count = self._count_general_links(content)
                return 'custom_html', link_count, content_type
                
        except Exception:
            return 'unknown', 0, 'text/html'
    
    def _is_directory_listing(self, content: str) -> bool:
        """Check if content is a directory listing."""
        patterns = [
            r'<title>.*Directory listing.*</title>',
            r'<h1>.*Directory listing.*</h1>',
            r'<h1>.*Index of.*</h1>',
            r'Parent Directory',
            r'<a href="\.\./?">\.\./</a>'
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _is_api_response(self, content: str, content_type: str) -> bool:
        """Check if response is API (JSON/XML)."""
        return 'json' in content_type.lower() or 'xml' in content_type.lower()
    
    def _count_directory_links(self, content: str) -> int:
        """Count links in directory listing."""
        # Look for href patterns excluding parent directory
        links = re.findall(r'<a href="([^"]+)"[^>]*>', content, re.IGNORECASE)
        # Filter out parent directory and non-file links
        valid_links = [link for link in links if not link.startswith('../') and link != '/']
        return len(valid_links)
    
    def _count_general_links(self, content: str) -> int:
        """Count general links in HTML content."""
        links = re.findall(r'<a href="([^"]+)"[^>]*>', content, re.IGNORECASE)
        # Filter out external links and anchors
        internal_links = [link for link in links if not link.startswith(('http://', 'https://', 'mailto:', '#'))]
        return len(internal_links) 