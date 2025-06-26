"""
Python requests-based download strategy implementation.
"""

import os
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Set, List, Tuple
from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus


class PythonDownloader(BaseDownloader):
    """Download strategy using Python requests with multi-threading."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent
        })
        self.downloaded_urls = set()
        self.failed_urls = set()
        self.total_size = 0
        self.lock = threading.Lock()
    
    def download(self, url: str, output_dir: str) -> DownloadResult:
        """Download using Python requests with recursive crawling."""
        start_time = time.time()
        
        if not self._create_output_directory(output_dir):
            return DownloadResult(
                status=DownloadStatus.FAILED,
                downloaded_files=0,
                failed_files=0,
                total_size=0,
                elapsed_time=0,
                output_directory=output_dir,
                error_message="Failed to create output directory"
            )
        
        try:
            self._report_progress("Starting Python-based download...", 0.0)
            
            # Discover all URLs to download
            all_urls = self._discover_urls(url)
            
            if not all_urls:
                return DownloadResult(
                    status=DownloadStatus.FAILED,
                    downloaded_files=0,
                    failed_files=0,
                    total_size=0,
                    elapsed_time=time.time() - start_time,
                    output_directory=output_dir,
                    error_message="No downloadable URLs found"
                )
            
            # Download files with thread pool
            self._download_files_parallel(all_urls, output_dir, url)
            
            elapsed_time = time.time() - start_time
            
            self._report_progress("Download completed", 1.0)
            
            return DownloadResult(
                status=DownloadStatus.COMPLETED,
                downloaded_files=len(self.downloaded_urls),
                failed_files=len(self.failed_urls),
                total_size=self.total_size,
                elapsed_time=elapsed_time,
                output_directory=output_dir
            )
            
        except Exception as e:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                downloaded_files=len(self.downloaded_urls),
                failed_files=len(self.failed_urls),
                total_size=self.total_size,
                elapsed_time=time.time() - start_time,
                output_directory=output_dir,
                error_message=str(e)
            )
    
    def supports(self, server_info) -> bool:
        """Python downloader supports all server types."""
        return True
    
    def get_priority(self) -> int:
        """Python downloader has medium priority."""
        return 2
    
    def _discover_urls(self, base_url: str, max_depth: int = 5) -> Set[str]:
        """Recursively discover all downloadable URLs."""
        discovered = set()
        to_visit = [(base_url, 0)]
        visited = set()
        
        while to_visit and not self.is_cancelled:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth >= max_depth:
                continue
            
            visited.add(current_url)
            
            try:
                response = self.session.get(current_url, timeout=self.config.timeout)
                response.raise_for_status()
                
                if self._is_html_content(response):
                    # Parse HTML and extract links
                    soup = BeautifulSoup(response.content, 'html.parser')
                    links = self._extract_links(soup, current_url)
                    
                    for link_url, is_directory in links:
                        if is_directory:
                            # Add directory to visit queue
                            to_visit.append((link_url, depth + 1))
                        else:
                            # Add file to download list
                            filename = os.path.basename(urlparse(link_url).path)
                            if self._should_download_file(filename, link_url):
                                discovered.add(link_url)
                else:
                    # Direct file URL
                    filename = os.path.basename(urlparse(current_url).path)
                    if self._should_download_file(filename, current_url):
                        discovered.add(current_url)
                        
            except Exception as e:
                self._report_progress(f"Error discovering {current_url}: {str(e)}")
                continue
        
        return discovered
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Tuple[str, bool]]:
        """Extract links from HTML soup."""
        links = []
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            
            # Skip certain types of links
            if href.startswith(('#', 'mailto:', 'javascript:')):
                continue
            
            # Convert to absolute URL
            full_url = urljoin(base_url, href)
            
            # Check if it's the same domain
            if not self._is_same_domain(base_url, full_url):
                continue
            
            # Determine if it's a directory
            is_directory = href.endswith('/') or self._looks_like_directory(link_tag.get_text())
            
            links.append((full_url, is_directory))
        
        return links
    
    def _download_files_parallel(self, urls: Set[str], output_dir: str, base_url: str):
        """Download files using thread pool."""
        with ThreadPoolExecutor(max_workers=self.config.max_threads) as executor:
            # Submit download tasks
            future_to_url = {
                executor.submit(self._download_single_file, url, output_dir, base_url): url
                for url in urls
            }
            
            completed = 0
            total = len(urls)
            
            for future in as_completed(future_to_url):
                if self.is_cancelled:
                    break
                
                url = future_to_url[future]
                try:
                    success, size = future.result()
                    if success:
                        with self.lock:
                            self.downloaded_urls.add(url)
                            self.total_size += size
                    else:
                        with self.lock:
                            self.failed_urls.add(url)
                except Exception as e:
                    with self.lock:
                        self.failed_urls.add(url)
                    self._report_progress(f"Error downloading {url}: {str(e)}")
                
                completed += 1
                progress = completed / total
                self._report_progress(f"Downloaded {completed}/{total} files", progress)
    
    def _download_single_file(self, url: str, output_dir: str, base_url: str) -> Tuple[bool, int]:
        """Download a single file."""
        try:
            # Determine local file path
            local_path = self._get_local_path(url, base_url, output_dir)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Skip if file exists and not overwriting
            if os.path.exists(local_path) and not self.config.overwrite_existing:
                return True, os.path.getsize(local_path)
            
            # Download file
            response = self.session.get(url, timeout=self.config.timeout, stream=True)
            response.raise_for_status()
            
            # Check file size limit
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.config.max_file_size:
                return False, 0
            
            # Write file
            total_size = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_cancelled:
                        break
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            return True, total_size
            
        except Exception:
            return False, 0
    
    def _get_local_path(self, url: str, base_url: str, output_dir: str) -> str:
        """Generate local file path for a URL."""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        
        # Get relative path
        if parsed_url.path.startswith(parsed_base.path):
            rel_path = parsed_url.path[len(parsed_base.path):].lstrip('/')
        else:
            rel_path = parsed_url.path.lstrip('/')
        
        # Decode URL encoding and make safe
        import urllib.parse
        rel_path = urllib.parse.unquote(rel_path)
        rel_path = self._get_safe_filename(rel_path)
        
        return os.path.join(output_dir, rel_path)
    
    def _is_html_content(self, response: requests.Response) -> bool:
        """Check if response contains HTML content."""
        content_type = response.headers.get('Content-Type', '').lower()
        return 'text/html' in content_type
    
    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        """Check if two URLs are from the same domain."""
        base_domain = urlparse(base_url).netloc
        target_domain = urlparse(target_url).netloc
        return base_domain == target_domain
    
    def _looks_like_directory(self, text: str) -> bool:
        """Check if link text suggests it's a directory."""
        indicators = ['[dir]', '[folder]', '📁', '🗂️', 'directory']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators) 