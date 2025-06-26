#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys


class ConfigManager:
    """配置管理器 - 负责配置文件的读取、写入和验证"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = {}
        self._load_config()
    
    def _get_cpu_count(self):
        """获取CPU核数"""
        try:
            return os.cpu_count() or 4
        except:
            return 4
    
    def _get_default_config(self):
        """生成基于系统环境的智能默认配置"""
        cpu_count = self._get_cpu_count()
        
        return {
            "download": {
                "max_workers": cpu_count * 2,
                "chunk_size": 8192,
                "timeout": 30,
                "retries": 3,
                "delay_between_requests": 0.1,
                "max_file_size": "1GB",
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            },
            "filters": {
                "exclude_extensions": [".tmp", ".log", ".bak"],
                "exclude_patterns": ["*.tmp", "*.log", "*.bak", ".*"],
                "include_extensions": [],
                "max_depth": 10
            },
            "output": {
                "create_index": True,
                "preserve_timestamps": True,
                "create_directory_structure": True,
                "log_level": "INFO"
            },
            "network": {
                "verify_ssl": True,
                "follow_redirects": True,
                "max_redirects": 5,
                "connection_pool_size": cpu_count * 2
            },
            "system": {
                "cpu_cores": cpu_count,
                "auto_generated": True,
                "version": "1.0.0"
            }
        }
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = self._get_default_config()
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print("✅ 已创建默认配置文件: {}".format(self.config_path))
            print("📊 检测到 {} 个CPU核心".format(default_config['system']['cpu_cores']))
            print("🚀 默认线程数设置为: {}".format(default_config['download']['max_workers']))
            return default_config
        except Exception as e:
            print("❌ 创建默认配置文件失败: {}".format(e))
            return self._get_default_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            print("⚠️ 配置文件 {} 不存在，正在创建默认配置...".format(self.config_path))
            self.config = self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            current_cpu_count = self._get_cpu_count()
            if (loaded_config.get('system', {}).get('cpu_cores') != current_cpu_count or
                not loaded_config.get('system', {}).get('auto_generated')):
                print("🔄 检测到系统变化，更新配置文件...")
                self.config = self._update_config_for_system(loaded_config)
                self._save_config()
            else:
                self.config = loaded_config
                
        except json.JSONDecodeError as e:
            print("❌ 配置文件格式错误: {}".format(e))
            print("🔧 正在重新创建配置文件...")
            self.config = self._create_default_config()
        except Exception as e:
            print("❌ 加载配置文件失败: {}".format(e))
            print("🔧 使用默认配置...")
            self.config = self._get_default_config()
    
    def _update_config_for_system(self, old_config):
        """根据当前系统环境更新配置"""
        default_config = self._get_default_config()
        updated_config = old_config.copy()
        updated_config['system'] = default_config['system']
        
        if (updated_config.get('download', {}).get('max_workers') == 
            old_config.get('system', {}).get('cpu_cores', 4) * 2):
            updated_config.setdefault('download', {})['max_workers'] = default_config['download']['max_workers']
        
        updated_config.setdefault('network', {})['connection_pool_size'] = default_config['network']['connection_pool_size']
        return updated_config
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("❌ 保存配置文件失败: {}".format(e))
    
    def get(self, key, default=None):
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def get_download_config(self):
        """获取下载相关配置"""
        return self.get('download', {})
    
    def get_filter_config(self):
        """获取过滤相关配置"""
        return self.get('filters', {})
    
    def get_output_config(self):
        """获取输出相关配置"""
        return self.get('output', {})
    
    def get_network_config(self):
        """获取网络相关配置"""
        return self.get('network', {})
    
    def parse_size(self, size_str):
        """解析大小字符串，如 '10MB', '1GB' 等"""
        if not size_str:
            return 0
        
        size_str = size_str.upper().strip()
        size_num = ""
        unit = ""
        
        for char in size_str:
            if char.isdigit() or char == '.':
                size_num += char
            else:
                unit = size_str[len(size_num):].strip()
                break
        
        try:
            size = float(size_num) if size_num else 0
        except ValueError:
            return 0
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        return int(size * multipliers.get(unit, 1))
    
    def validate_config(self):
        """验证配置文件的有效性"""
        required_keys = [
            'download.max_workers',
            'download.timeout',
            'download.retries'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                print("❌ 配置验证失败: 缺少必需的配置项 {}".format(key))
                return False
        
        max_workers = self.get('download.max_workers', 1)
        if not isinstance(max_workers, int) or max_workers < 1:
            print("❌ 配置验证失败: max_workers 必须是大于0的整数")
            return False
        
        return True
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("📋 当前配置摘要:")
        print("   CPU核数: {}".format(self.get('system.cpu_cores', 'unknown')))
        print("   下载线程数: {}".format(self.get('download.max_workers', 'unknown')))
        print("   连接超时: {}秒".format(self.get('download.timeout', 'unknown')))
        print("   重试次数: {}".format(self.get('download.retries', 'unknown')))
        print("   SSL验证: {}".format('启用' if self.get('network.verify_ssl', True) else '禁用'))
