"""
File utility functions for smart downloader.
"""

import os
import re
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
import urllib.parse


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def create_directory(path: str) -> bool:
        """
        Create directory if it doesn't exist.
        
        Args:
            path: Directory path to create
            
        Returns:
            True if successful
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Convert filename to filesystem-safe format.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        # URL decode first
        filename = urllib.parse.unquote(filename)
        
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        safe_filename = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        safe_filename = safe_filename.strip(' .')
        
        # Limit length (Windows has 255 char limit)
        if len(safe_filename) > 255:
            name, ext = FileUtils.split_filename(safe_filename)
            max_name_len = 255 - len(ext) - 1 if ext else 255
            safe_filename = name[:max_name_len] + ('.' + ext if ext else '')
        
        # Ensure not empty
        if not safe_filename:
            safe_filename = 'unnamed_file'
        
        return safe_filename
    
    @staticmethod
    def split_filename(filename: str) -> Tuple[str, str]:
        """
        Split filename into name and extension.
        
        Args:
            filename: Filename to split
            
        Returns:
            Tuple of (name, extension)
        """
        if '.' in filename:
            parts = filename.rsplit('.', 1)
            return parts[0], parts[1]
        return filename, ''
    
    @staticmethod
    def get_unique_filename(filepath: str) -> str:
        """
        Get unique filename if file already exists.
        
        Args:
            filepath: Original file path
            
        Returns:
            Unique file path
        """
        if not os.path.exists(filepath):
            return filepath
        
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = FileUtils.split_filename(filename)
        
        counter = 1
        while True:
            new_filename = f"{name}_{counter}.{ext}" if ext else f"{name}_{counter}"
            new_filepath = os.path.join(directory, new_filename)
            
            if not os.path.exists(new_filepath):
                return new_filepath
            
            counter += 1
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            filepath: Path to file
            
        Returns:
            File size in bytes, 0 if error
        """
        try:
            return os.path.getsize(filepath)
        except Exception:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
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
    
    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'md5') -> str:
        """
        Calculate file hash.
        
        Args:
            filepath: Path to file
            algorithm: Hash algorithm (md5, sha1, sha256)
            
        Returns:
            File hash as hex string
        """
        try:
            hash_func = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception:
            return ''
    
    @staticmethod
    def is_binary_file(filepath: str) -> bool:
        """
        Check if file is binary.
        
        Args:
            filepath: Path to file
            
        Returns:
            True if binary file
        """
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return False
    
    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        Calculate total size of directory.
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += FileUtils.get_file_size(filepath)
        except Exception:
            pass
        return total_size
    
    @staticmethod
    def count_files_in_directory(directory: str) -> int:
        """
        Count files in directory recursively.
        
        Args:
            directory: Directory path
            
        Returns:
            Number of files
        """
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                count += len(filenames)
        except Exception:
            pass
        return count
    
    @staticmethod
    def create_relative_path(base_path: str, target_path: str) -> str:
        """
        Create relative path from base to target.
        
        Args:
            base_path: Base directory path
            target_path: Target file/directory path
            
        Returns:
            Relative path
        """
        try:
            return os.path.relpath(target_path, base_path)
        except Exception:
            return target_path
    
    @staticmethod
    def copy_file(source: str, destination: str) -> bool:
        """
        Copy file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            FileUtils.create_directory(dest_dir)
            
            shutil.copy2(source, destination)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        """
        Move file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination)
            FileUtils.create_directory(dest_dir)
            
            shutil.move(source, destination)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_file(filepath: str) -> bool:
        """
        Delete file safely.
        
        Args:
            filepath: File path to delete
            
        Returns:
            True if successful
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_directory(directory: str) -> bool:
        """
        Delete directory and all contents.
        
        Args:
            directory: Directory path to delete
            
        Returns:
            True if successful
        """
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            return True
        except Exception:
            return False
    
    @staticmethod
    def find_files_by_extension(directory: str, extension: str) -> List[str]:
        """
        Find all files with specific extension in directory.
        
        Args:
            directory: Directory to search
            extension: File extension (without dot)
            
        Returns:
            List of file paths
        """
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.lower().endswith(f'.{extension.lower()}'):
                        files.append(os.path.join(root, filename))
        except Exception:
            pass
        return files
    
    @staticmethod
    def get_temp_directory() -> str:
        """
        Get system temporary directory.
        
        Returns:
            Temporary directory path
        """
        import tempfile
        return tempfile.gettempdir()
    
    @staticmethod
    def create_temp_file(suffix: str = '', prefix: str = 'tmp') -> str:
        """
        Create temporary file.
        
        Args:
            suffix: File suffix
            prefix: File prefix
            
        Returns:
            Temporary file path
        """
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return path 