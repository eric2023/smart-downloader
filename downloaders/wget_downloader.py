"""
Wget-based download strategy implementation.
"""

import subprocess
import os
import time
import re
from typing import List
from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus


class WgetDownloader(BaseDownloader):
    """Download strategy using wget command-line tool."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.process = None
    
    def download(self, url: str, output_dir: str) -> DownloadResult:
        """Download using wget with recursive options."""
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
        
        # Build wget command
        cmd = self._build_wget_command(url, output_dir)
        
        try:
            self._report_progress("Starting wget download...", 0.0)
            
            # Execute wget command
            result = subprocess.run(
                cmd,
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeout * 60  # Convert to minutes
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parse wget output for statistics
                stats = self._parse_wget_output(result.stderr)
                
                self._report_progress("Download completed successfully", 1.0)
                
                return DownloadResult(
                    status=DownloadStatus.COMPLETED,
                    downloaded_files=stats['downloaded_files'],
                    failed_files=stats['failed_files'],
                    total_size=stats['total_size'],
                    elapsed_time=elapsed_time,
                    output_directory=output_dir,
                    detailed_log=result.stderr.split('\n')
                )
            else:
                return DownloadResult(
                    status=DownloadStatus.FAILED,
                    downloaded_files=0,
                    failed_files=0,
                    total_size=0,
                    elapsed_time=elapsed_time,
                    output_directory=output_dir,
                    error_message=result.stderr,
                    detailed_log=result.stderr.split('\n')
                )
                
        except subprocess.TimeoutExpired:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                downloaded_files=0,
                failed_files=0,
                total_size=0,
                elapsed_time=time.time() - start_time,
                output_directory=output_dir,
                error_message="Download timed out"
            )
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
        """Check if wget can handle this server type."""
        # Wget supports most HTTP servers
        supported_types = ['apache', 'nginx', 'simplehttp', 'iis', 'unknown']
        supported_structures = ['directory_listing', 'custom_html']
        
        return (server_info.server_type in supported_types and 
                server_info.page_structure in supported_structures)
    
    def get_priority(self) -> int:
        """Wget has high priority for supported servers."""
        return 1
    
    def _build_wget_command(self, url: str, output_dir: str) -> List[str]:
        """Build the wget command with appropriate options."""
        cmd = [
            'wget',
            '--recursive',                    # Recursive download
            '--no-parent',                   # Don't go to parent directories
            '--convert-links',               # Convert links for local viewing
            '--adjust-extension',            # Add proper extensions
            '--page-requisites',             # Download CSS, images, etc.
            '--no-check-certificate',       # Skip SSL certificate check
            '--restrict-file-names=windows', # Use Windows-compatible filenames
            '--tries=' + str(self.config.retry_attempts),
            '--timeout=' + str(self.config.timeout),
            '--user-agent=' + self.config.user_agent,
            '--progress=bar:force',          # Show progress bar
        ]
        
        # Add thread control
        if self.config.max_threads > 1:
            cmd.extend(['--limit-rate=0'])  # Remove rate limiting for parallel
        
        # Add file size limit
        if self.config.max_file_size:
            cmd.extend(['--quota=' + str(self.config.max_file_size)])
        
        # Add exclusion patterns
        if self.config.exclude_extensions:
            for ext in self.config.exclude_extensions:
                cmd.extend(['--reject', f'*.{ext}'])
        
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['--exclude-directories', pattern])
        
        # Overwrite behavior
        if not self.config.overwrite_existing:
            cmd.append('--no-clobber')
        
        # Add the URL
        cmd.append(url)
        
        return cmd
    
    def _parse_wget_output(self, output: str) -> dict:
        """Parse wget output to extract download statistics."""
        stats = {
            'downloaded_files': 0,
            'failed_files': 0,
            'total_size': 0
        }
        
        try:
            # Count downloaded files
            downloaded_matches = re.findall(r'saved \[(\d+)/(\d+)\]', output)
            if downloaded_matches:
                stats['downloaded_files'] = len(downloaded_matches)
                stats['total_size'] = sum(int(match[0]) for match in downloaded_matches)
            
            # Count failed downloads
            failed_matches = re.findall(r'ERROR|FAILED|404|403', output, re.IGNORECASE)
            stats['failed_files'] = len(failed_matches)
            
        except Exception:
            # If parsing fails, return default values
            pass
        
        return stats
    
    def cancel(self):
        """Cancel the wget process."""
        super().cancel()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def is_available(self) -> bool:
        """Check if wget is available on the system."""
        try:
            result = subprocess.run(['wget', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False 