"""
Configuration wrapper to convert dict to object attributes.
"""


class ConfigWrapper:
    """Wrapper to convert dictionary config to object with attributes."""
    
    def __init__(self, config_dict):
        self._config = config_dict
        
        # Extract common attributes from nested config
        self.user_agent = self._get_nested('download', 'user_agent', 
                                          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        self.timeout = self._get_nested('download', 'timeout', 30)
        self.max_threads = self._get_nested('download', 'max_workers', 16)
        self.retry_attempts = self._get_nested('download', 'retry_attempts', 3)
        self.max_file_size = self._get_nested('download', 'max_file_size', None)
        self.overwrite_existing = self._get_nested('download', 'overwrite_existing', True)
        
        # Filter settings
        self.exclude_extensions = self._get_nested('filters', 'exclude_extensions', [])
        self.include_patterns = self._get_nested('filters', 'include_patterns', [])
        self.exclude_patterns = self._get_nested('filters', 'exclude_patterns', [])
        
        # Network settings
        self.verify_ssl = self._get_nested('network', 'verify_ssl', True)
        
    def _get_nested(self, section, key, default=None):
        """Get value from nested dictionary structure."""
        return self._config.get(section, {}).get(key, default)
    
    def get(self, key, default=None):
        """Get value from config dictionary."""
        return self._config.get(key, default)
    
    def __getattr__(self, name):
        """Fallback to dictionary access if attribute not found."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") 