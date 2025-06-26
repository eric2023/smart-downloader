"""
Page analyzer module for detailed page structure analysis.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass


@dataclass
class LinkInfo:
    """Information about a discovered link."""
    url: str
    text: str
    is_directory: bool
    file_extension: str
    estimated_size: int


class PageAnalyzer:
    """Analyzes web page structure and extracts downloadable links."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartDownloader/1.0 (Compatible; Analysis Bot)'
        })
    
    def analyze_page(self, url: str) -> Dict:
        """Perform comprehensive page analysis."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = self._extract_links(soup, url)
            structure = self._analyze_structure(soup)
            metadata = self._extract_metadata(soup, response.headers)
            
            return {
                'links': links,
                'structure': structure,
                'metadata': metadata,
                'total_links': len(links),
                'directories': len([l for l in links if l.is_directory]),
                'files': len([l for l in links if not l.is_directory])
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'links': [],
                'structure': 'unknown',
                'metadata': {},
                'total_links': 0,
                'directories': 0,
                'files': 0
            }
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[LinkInfo]:
        """Extract all downloadable links from the page."""
        links = []
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            text = link_tag.get_text(strip=True)
            
            # Skip certain types of links
            if self._should_skip_link(href):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Determine if it's a directory
            is_directory = href.endswith('/') or self._looks_like_directory(text, href)
            
            # Extract file extension
            file_extension = self._get_file_extension(href)
            
            # Estimate size (placeholder)
            estimated_size = 0
            
            links.append(LinkInfo(
                url=full_url,
                text=text,
                is_directory=is_directory,
                file_extension=file_extension,
                estimated_size=estimated_size
            ))
        
        return links
    
    def _should_skip_link(self, href: str) -> bool:
        """Determine if a link should be skipped."""
        skip_patterns = [
            r'^https?://',  # External links
            r'^mailto:',    # Email links
            r'^#',          # Anchors
            r'^\?',         # Query parameters only
            r'^\.\.$',      # Parent directory
            r'^/$'          # Root directory
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, href):
                return True
        
        return False
    
    def _looks_like_directory(self, text: str, href: str) -> bool:
        """Determine if a link looks like a directory."""
        directory_indicators = [
            href.endswith('/'),
            '[DIR]' in text.upper(),
            'DIRECTORY' in text.upper(),
            '📁' in text,
            '🗂️' in text,
            not self._get_file_extension(href)  # No file extension
        ]
        
        return any(directory_indicators)
    
    def _get_file_extension(self, href: str) -> str:
        """Extract file extension from URL."""
        # Remove query parameters and fragments
        clean_href = href.split('?')[0].split('#')[0]
        
        # Extract extension
        if '.' in clean_href:
            return clean_href.split('.')[-1].lower()
        return ''
    
    def _analyze_structure(self, soup: BeautifulSoup) -> str:
        """Analyze the overall structure of the page."""
        title = soup.find('title')
        if title:
            title_text = title.get_text().lower()
            
            if 'directory listing' in title_text or 'index of' in title_text:
                return 'directory_listing'
            elif 'file browser' in title_text or 'file manager' in title_text:
                return 'file_browser'
        
        # Check for common directory listing patterns
        if soup.find('pre'):  # Simple HTTP server style
            return 'simple_listing'
        elif soup.find('table'):  # Table-based listing
            return 'table_listing'
        elif soup.find('ul') or soup.find('ol'):  # List-based
            return 'list_structure'
        else:
            return 'custom_layout'
    
    def _extract_metadata(self, soup: BeautifulSoup, headers: Dict) -> Dict:
        """Extract useful metadata from page and headers."""
        metadata = {}
        
        # From HTML
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[f'meta_{name}'] = content
        
        # From HTTP headers
        metadata['server'] = headers.get('Server', 'Unknown')
        metadata['content_type'] = headers.get('Content-Type', 'Unknown')
        metadata['last_modified'] = headers.get('Last-Modified', 'Unknown')
        
        return metadata
    
    def get_file_tree(self, url: str, max_depth: int = 3) -> Dict:
        """Build a file tree structure by recursively analyzing directories."""
        def _build_tree(current_url: str, current_depth: int) -> Dict:
            if current_depth >= max_depth:
                return {'truncated': True}
            
            analysis = self.analyze_page(current_url)
            tree = {
                'url': current_url,
                'files': [],
                'directories': {},
                'metadata': analysis.get('metadata', {})
            }
            
            for link in analysis.get('links', []):
                if link.is_directory:
                    # Recursively analyze subdirectories
                    tree['directories'][link.text] = _build_tree(link.url, current_depth + 1)
                else:
                    tree['files'].append({
                        'name': link.text,
                        'url': link.url,
                        'extension': link.file_extension,
                        'estimated_size': link.estimated_size
                    })
            
            return tree
        
        return _build_tree(url, 0) 