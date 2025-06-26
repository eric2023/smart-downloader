"""
Logging utility for smart downloader.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """Centralized logging utility."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self, 
                     level: str = 'INFO',
                     log_file: str = 'smart_downloader.log',
                     max_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5,
                     console_output: bool = True):
        """Setup the logger with specified configuration."""
        
        # Create logger
        self._logger = logging.getLogger('SmartDownloader')
        self._logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        if log_file:
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def reconfigure(self, config: dict):
        """Reconfigure logger with new settings."""
        self._setup_logger(
            level=config.get('level', 'INFO'),
            log_file=config.get('file', 'smart_downloader.log'),
            max_size=self._parse_size(config.get('max_size', '10MB')),
            backup_count=config.get('backup_count', 5),
            console_output=config.get('console_output', True)
        )
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes."""
        if isinstance(size_str, int):
            return size_str
        
        size_str = str(size_str).upper()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        # Try exact matches first
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number_part = size_str[:-len(suffix)]
                try:
                    return int(number_part) * multiplier
                except ValueError:
                    break
        
        # Try partial matches (e.g., '10M' -> '10MB')
        partial_matches = {
            'K': 'KB',
            'M': 'MB', 
            'G': 'GB'
        }
        
        for partial, full in partial_matches.items():
            if size_str.endswith(partial):
                number_part = size_str[:-len(partial)]
                try:
                    return int(number_part) * multipliers[full]
                except ValueError:
                    break
        
        # If no suffix found, assume bytes
        try:
            return int(size_str)
        except ValueError:
            # Default to 10MB if parsing fails
            return 10 * 1024 * 1024
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self._logger.exception(message, *args, **kwargs)
    
    def log_download_start(self, url: str, output_dir: str, strategy: str):
        """Log download start."""
        self.info(f"Starting download: {url} -> {output_dir} using {strategy}")
    
    def log_download_progress(self, url: str, progress: float, message: str = ""):
        """Log download progress."""
        self.info(f"Download progress [{url}]: {progress:.1%} {message}")
    
    def log_download_complete(self, url: str, files_downloaded: int, 
                            total_size: int, elapsed_time: float):
        """Log download completion."""
        size_mb = total_size / (1024 * 1024)
        speed_mbps = size_mb / elapsed_time if elapsed_time > 0 else 0
        
        self.info(f"Download completed: {url}")
        self.info(f"Files downloaded: {files_downloaded}")
        self.info(f"Total size: {size_mb:.2f} MB")
        self.info(f"Time taken: {elapsed_time:.2f} seconds")
        self.info(f"Average speed: {speed_mbps:.2f} MB/s")
    
    def log_download_error(self, url: str, error: str):
        """Log download error."""
        self.error(f"Download failed: {url} - {error}")
    
    def log_server_analysis(self, url: str, server_type: str, 
                          page_structure: str, estimated_files: int):
        """Log server analysis results."""
        self.info(f"Server analysis: {url}")
        self.info(f"Server type: {server_type}")
        self.info(f"Page structure: {page_structure}")
        self.info(f"Estimated files: {estimated_files}")
    
    def log_strategy_selection(self, url: str, strategy: str, reason: str):
        """Log strategy selection."""
        self.info(f"Strategy selected for {url}: {strategy} - {reason}")
    
    def log_file_download(self, file_url: str, local_path: str, 
                         size: int, success: bool):
        """Log individual file download."""
        if success:
            self.debug(f"Downloaded: {file_url} -> {local_path} ({size} bytes)")
        else:
            self.warning(f"Failed to download: {file_url}")
    
    def log_system_info(self):
        """Log system information."""
        try:
            import platform
            import psutil
            
            self.info("System Information:")
            self.info(f"Platform: {platform.platform()}")
            self.info(f"Python: {platform.python_version()}")
            self.info(f"CPU cores: {psutil.cpu_count()}")
            self.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        except ImportError:
            self.info("System information unavailable (missing psutil)")
    
    def create_session_log(self, session_id: str):
        """Create a session-specific log entry."""
        self.info(f"=== Session {session_id} started at {datetime.now()} ===")
    
    def close_session_log(self, session_id: str):
        """Close a session-specific log entry."""
        self.info(f"=== Session {session_id} ended at {datetime.now()} ===")
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the current log file path."""
        for handler in self._logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                return handler.baseFilename
        return None
    
    def get_log_stats(self) -> dict:
        """Get logging statistics."""
        log_file = self.get_log_file_path()
        stats = {
            'log_file': log_file,
            'file_size': 0,
            'handlers': len(self._logger.handlers),
            'level': self._logger.level
        }
        
        if log_file and os.path.exists(log_file):
            stats['file_size'] = os.path.getsize(log_file)
        
        return stats


# Global logger instance
logger = Logger() 