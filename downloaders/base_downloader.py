"""
Base downloader class defining the interface for all download strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class DownloadStatus(Enum):
    """Download status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadResult:
    """Result of a download operation."""
    status: DownloadStatus
    downloaded_files: int
    failed_files: int
    total_size: int
    elapsed_time: float
    output_directory: str
    error_message: Optional[str] = None
    detailed_log: List[str] = None


class BaseDownloader(ABC):
    """Abstract base class for all download strategies."""
    
    def __init__(self, config=None):
        self.config = config
        self.is_cancelled = False
        self.progress_callback = None
    
    @abstractmethod
    def download(self, url: str, output_dir: str):
        """
        Download files from the given URL to the output directory.
        
        Args:
            url: The URL to download from
            output_dir: The directory to save files to
            
        Returns:
            DownloadResult with operation details
        """
        pass
    
    @abstractmethod
    def supports(self, server_info) -> bool:
        """
        Check if this downloader supports the given server type.
        
        Args:
            server_info: ServerInfo object with server details
            
        Returns:
            True if this downloader can handle the server
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Get the priority of this downloader (lower number = higher priority).
        
        Returns:
            Priority value (1-10, where 1 is highest priority)
        """
        pass
    
    def set_progress_callback(self, callback):
        """Set a callback function for progress updates."""
        self.progress_callback = callback
    
    def cancel(self):
        """Cancel the current download operation."""
        self.is_cancelled = True
    
    def is_available(self) -> bool:
        """
        Check if this downloader is available/functional.
        
        Returns:
            True if this downloader can be used
        """
        return True  # Default implementation - always available
    
    def get_name(self) -> str:
        """
        Get the name of this downloader.
        
        Returns:
            Name of the downloader
        """
        return self.__class__.__name__.replace('Downloader', '').lower()
    
    def _should_download_file(self, filename: str, file_url: str) -> bool:
        """
        Check if a file should be downloaded based on filters.
        
        Args:
            filename: Name of the file
            file_url: URL of the file
            
        Returns:
            True if file should be downloaded
        """
        if not self.config:
            return True
            
        # Check file extension exclusions
        if self.config.exclude_extensions:
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_ext in self.config.exclude_extensions:
                return False
        
        # Check include patterns
        if self.config.include_patterns:
            import re
            if not any(re.search(pattern, filename, re.IGNORECASE) 
                      for pattern in self.config.include_patterns):
                return False
        
        # Check exclude patterns
        if self.config.exclude_patterns:
            import re
            if any(re.search(pattern, filename, re.IGNORECASE) 
                  for pattern in self.config.exclude_patterns):
                return False
        
        return True
    
    def _create_output_directory(self, path: str) -> bool:
        """
        Create output directory if it doesn't exist.
        
        Args:
            path: Directory path to create
            
        Returns:
            True if directory was created or already exists
        """
        import os
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    def _get_safe_filename(self, filename: str) -> str:
        """
        Convert filename to a safe format for the filesystem.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        import re
        import urllib.parse
        
        # URL decode first
        filename = urllib.parse.unquote(filename)
        
        # Replace invalid characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(safe_chars) > 255:
            name, ext = safe_chars.rsplit('.', 1) if '.' in safe_chars else (safe_chars, '')
            safe_chars = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        return safe_chars
    
    def _report_progress(self, message: str, progress: float = None):
        """
        Report progress to the callback if set.
        
        Args:
            message: Progress message
            progress: Progress percentage (0.0 to 1.0)
        """
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB" 