"""
Hybrid download strategy that combines multiple approaches.
"""

import os
import time
from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus
from .wget_downloader import WgetDownloader
from .python_downloader import PythonDownloader


class HybridDownloader(BaseDownloader):
    """Hybrid strategy that selects the best approach dynamically."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.wget_downloader = WgetDownloader(config)
        self.python_downloader = PythonDownloader(config)
    
    def download(self, url: str, output_dir: str) -> DownloadResult:
        """Download using the best strategy for the given situation."""
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
            # Analyze the target to choose strategy
            strategy = self._choose_strategy(url)
            
            self._report_progress(f"Using {strategy.__class__.__name__} strategy", 0.1)
            
            # Set progress callback for the chosen strategy
            strategy.set_progress_callback(self.progress_callback)
            
            # Perform download
            result = strategy.download(url, output_dir)
            
            # If first strategy fails, try fallback
            if result.status == DownloadStatus.FAILED:
                fallback_strategy = self._get_fallback_strategy(strategy)
                if fallback_strategy:
                    self._report_progress(f"Falling back to {fallback_strategy.__class__.__name__}", 0.2)
                    fallback_strategy.set_progress_callback(self.progress_callback)
                    result = fallback_strategy.download(url, output_dir)
            
            return result
            
        except Exception as e:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                downloaded_files=0,
                failed_files=0,
                total_size=0,
                elapsed_time=time.time() - start_time,
                output_directory=output_dir,
                error_message=str(e)
            )
    
    def supports(self, server_info) -> bool:
        """Hybrid downloader supports all server types."""
        return True
    
    def get_priority(self) -> int:
        """Hybrid downloader has lowest priority (used as fallback)."""
        return 3
    
    def _choose_strategy(self, url: str):
        """Choose the best download strategy based on analysis."""
        # Quick analysis of the URL and server
        strategy_scores = {}
        
        try:
            # Test server response
            import requests
            response = requests.head(url, timeout=10)
            server_header = response.headers.get('Server', '').lower()
            content_length = response.headers.get('Content-Length')
            
            # Score wget strategy
            wget_score = 0
            if WgetDownloader.is_available():
                wget_score += 50  # Base score for availability
                
                # Wget is excellent for standard web servers
                if any(server in server_header for server in ['apache', 'nginx']):
                    wget_score += 30
                
                # Wget handles large downloads well
                if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB+
                    wget_score += 20
                
                # Wget is fast for many small files
                if self._estimate_file_count(url) > 50:
                    wget_score += 15
            
            strategy_scores['wget'] = wget_score
            
            # Score Python strategy
            python_score = 40  # Base score (always available)
            
            # Python is better for complex pages
            if 'simplehttp' not in server_header and 'python' not in server_header:
                python_score += 20
            
            # Python handles authentication and cookies better
            if self._needs_session_handling(url):
                python_score += 25
            
            # Python is better for selective downloading
            if self.config.exclude_patterns or self.config.include_patterns:
                python_score += 15
            
            strategy_scores['python'] = python_score
            
            # Choose strategy with highest score
            best_strategy = max(strategy_scores, key=strategy_scores.get)
            
            if best_strategy == 'wget' and wget_score > 0:
                return self.wget_downloader
            else:
                return self.python_downloader
                
        except Exception:
            # If analysis fails, default to Python strategy
            return self.python_downloader
    
    def _get_fallback_strategy(self, primary_strategy):
        """Get fallback strategy if primary fails."""
        if isinstance(primary_strategy, WgetDownloader):
            return self.python_downloader
        elif isinstance(primary_strategy, PythonDownloader):
            if WgetDownloader.is_available():
                return self.wget_downloader
        return None
    
    def _estimate_file_count(self, url: str) -> int:
        """Estimate the number of files to download."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Count links that look like files
            file_links = 0
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.endswith('/') and '.' in href:
                    file_links += 1
            
            return file_links
            
        except Exception:
            return 0
    
    def _needs_session_handling(self, url: str) -> bool:
        """Check if the site needs special session handling."""
        try:
            import requests
            
            # Check for authentication requirements
            response = requests.get(url, timeout=10)
            
            # Look for login forms or authentication headers
            if response.status_code == 401:
                return True
            
            if 'login' in response.text.lower() or 'authentication' in response.text.lower():
                return True
            
            # Check for cookies or session requirements
            if response.cookies:
                return True
            
            return False
            
        except Exception:
            return False
    
    def cancel(self):
        """Cancel the current download operation."""
        super().cancel()
        self.wget_downloader.cancel()
        self.python_downloader.cancel()
    
    def set_progress_callback(self, callback):
        """Set progress callback for all strategies."""
        super().set_progress_callback(callback)
        self.wget_downloader.set_progress_callback(callback)
        self.python_downloader.set_progress_callback(callback) 