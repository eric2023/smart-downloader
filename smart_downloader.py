#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import ConfigManager
from utils.config_wrapper import ConfigWrapper
from utils.logger import Logger
from detectors.server_detector import ServerDetector
from detectors.page_analyzer import PageAnalyzer
from downloaders.wget_downloader import WgetDownloader
from downloaders.python_downloader import PythonDownloader
from downloaders.hybrid_downloader import HybridDownloader
from utils.url_utils import URLUtils
from utils.file_utils import FileUtils


class SmartDownloader:
    """智能下载器主控制器"""
    
    def __init__(self, config_file="config.json"):
        # 处理配置文件路径 - 如果是相对路径，基于当前工作目录
        if not os.path.isabs(config_file):
            # 如果在包内执行，使用当前工作目录
            config_file = os.path.join(os.getcwd(), config_file)
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.config
        self.logger = Logger()
        
        # 重新配置Logger
        log_config = self.config.get('output', {})
        if log_config:
            self.logger.reconfigure({
                'level': log_config.get('log_level', 'INFO'),
                'file': log_config.get('log_file', 'smart_downloader.log'),
                'console_output': log_config.get('console_output', True)
            })
        
        # 打印配置摘要
        self.config_manager.print_config_summary()
        
        # 初始化检测器
        self.server_detector = ServerDetector()
        self.page_analyzer = PageAnalyzer()
        
        # 初始化下载器 - 使用配置包装器
        config_wrapper = ConfigWrapper(self.config)
        self.wget_downloader = WgetDownloader(config_wrapper)
        self.python_downloader = PythonDownloader(config_wrapper)
        self.hybrid_downloader = HybridDownloader(config_wrapper)
    
    def analyze(self, url):
        """
        分析目标URL
        
        Args:
            url: 目标URL
            
        Returns:
            分析结果字典
        """
        if not URLUtils.is_valid_url(url):
            self.logger.error("Invalid URL: {}".format(url))
            return {'success': False, 'error': 'Invalid URL'}
        
        try:
            self.logger.info("Analyzing target server: {}".format(url))
            
            # 服务器检测
            server_info = self.server_detector.detect_server_type(url)
            
            # 页面分析
            page_info = self.page_analyzer.analyze_structure(url)
            
            # 估算文件数量
            estimated_files = len(page_info.get('links', []))
            
            result = {
                'success': True,
                'url': url,
                'server_type': server_info.get('server_type', 'unknown'),
                'page_structure': page_info.get('structure_type', 'unknown'),
                'estimated_files': estimated_files,
                'estimated_size': server_info.get('estimated_size', 0),
                'response_time': server_info.get('response_time', 0),
                'supports_range': server_info.get('supports_range', False)
            }
            
            self.logger.info("Server analysis: {}".format(url))
            self.logger.info("Server type: {}".format(result['server_type']))
            self.logger.info("Page structure: {}".format(result['page_structure']))
            self.logger.info("Estimated files: {}".format(result['estimated_files']))
            
            return result
            
        except Exception as e:
            self.logger.error("Analysis failed: {}".format(e))
            return {'success': False, 'error': str(e)}
    
    def download(self, url, output_dir="downloads", strategy=None):
        """
        执行下载
        
        Args:
            url: 目标URL
            output_dir: 输出目录
            strategy: 指定策略 ('wget', 'python', 'hybrid')
            
        Returns:
            下载结果字典
        """
        if not URLUtils.is_valid_url(url):
            self.logger.error("Invalid URL: {}".format(url))
            return {'success': False, 'error': 'Invalid URL'}
        
        # 确保输出目录存在
        FileUtils.ensure_dir(output_dir)
        
        try:
            # 第一阶段：分析服务器
            self.logger.info("Phase 1: Analyzing target server...")
            analysis = self.analyze(url)
            
            if not analysis['success']:
                return analysis
            
            # 第二阶段：选择策略
            self.logger.info("Phase 2: Selecting download strategy...")
            downloader = self._select_downloader(analysis, strategy)
            
            strategy_name = downloader.get_name()
            self.logger.info("Strategy selected for {}: {} - Based on server analysis".format(url, strategy_name))
            
            # 第三阶段：执行下载
            self.logger.info("Phase 3: Executing download...")
            success = downloader.download(url, output_dir)
            
            if success:
                self.logger.info("Download completed successfully: {}".format(url))
                return {
                    'success': True,
                    'url': url,
                    'output_dir': output_dir,
                    'strategy_used': strategy_name,
                    'server_analysis': analysis
                }
            else:
                self.logger.error("Download failed: {}".format(url))
                return {
                    'success': False,
                    'error': 'Download failed',
                    'url': url,
                    'strategy_used': strategy_name
                }
                
        except Exception as e:
            self.logger.error("Download error: {}".format(e))
            return {'success': False, 'error': str(e)}
    
    def _select_downloader(self, analysis, forced_strategy=None):
        """选择最适合的下载器"""
        
        if forced_strategy:
            strategy_map = {
                'wget': self.wget_downloader,
                'python': self.python_downloader,
                'hybrid': self.hybrid_downloader
            }
            
            downloader = strategy_map.get(forced_strategy.lower())
            if downloader and downloader.is_available():
                return downloader
            else:
                self.logger.warning("Requested strategy '{}' not available, using automatic selection".format(forced_strategy))
        
        # 自动选择策略
        server_type = analysis.get('server_type', 'unknown')
        
        # 优先级顺序：Python > Hybrid > Wget
        if self.python_downloader.is_available():
            return self.python_downloader
        elif self.hybrid_downloader.is_available():
            return self.hybrid_downloader
        elif self.wget_downloader.is_available():
            return self.wget_downloader
        else:
            self.logger.warning("No downloaders available, using Python downloader as fallback")
            return self.python_downloader


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description="智能递归下载工具 - 支持多种下载策略和智能服务器检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 smart_downloader.py --analyze http://example.com/data/
  python3 smart_downloader.py --download http://example.com/data/ --output ./downloads/
  python3 smart_downloader.py --download http://example.com/data/ --strategy python
        """
    )
    
    # 主要操作
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--analyze', metavar='URL', 
                       help='分析目标网站结构')
    group.add_argument('--download', metavar='URL', 
                       help='下载网站内容')
    
    # 可选参数
    parser.add_argument('--output', '-o', metavar='DIR', default='downloads',
                        help='输出目录 (默认: downloads)')
    parser.add_argument('--strategy', '-s', 
                        choices=['wget', 'python', 'hybrid'],
                        help='指定下载策略')
    parser.add_argument('--config', '-c', metavar='FILE', default='config.json',
                        help='配置文件路径')
    parser.add_argument('--workers', '-w', type=int, metavar='NUM',
                        help='指定线程数 (覆盖配置文件)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='启用详细日志输出')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式')
    parser.add_argument('--version', action='version', version='Smart Downloader 1.0.0')
    
    args = parser.parse_args()
    
    try:
        # 创建下载器实例
        downloader = SmartDownloader(args.config)
        
        # 如果指定了线程数，更新配置
        if args.workers:
            downloader.config_manager.set('download.max_workers', args.workers)
            print("🔧 线程数设置为: {}".format(args.workers))
        
        # 执行操作
        if args.analyze:
            print("🔍 分析目标: {}".format(args.analyze))
            result = downloader.analyze(args.analyze)
            
            if result['success']:
                print("\n📊 分析结果:")
                print("   服务器类型: {}".format(result['server_type']))
                print("   页面结构: {}".format(result['page_structure']))
                print("   预估文件数: {}".format(result['estimated_files']))
                print("   响应时间: {:.2f}秒".format(result['response_time']))
                print("   支持Range请求: {}".format('是' if result['supports_range'] else '否'))
            else:
                print("❌ 分析失败: {}".format(result['error']))
                return 1
                
        elif args.download:
            print("📥 开始下载: {}".format(args.download))
            print("📁 输出目录: {}".format(args.output))
            
            if args.strategy:
                print("🎯 使用策略: {}".format(args.strategy))
            
            result = downloader.download(args.download, args.output, args.strategy)
            
            if result['success']:
                print("\n✅ 下载完成!")
                print("   使用策略: {}".format(result['strategy_used']))
                print("   输出目录: {}".format(result['output_dir']))
            else:
                print("❌ 下载失败: {}".format(result['error']))
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        return 1
    except Exception as e:
        print("❌ 程序错误: {}".format(e))
        return 1


if __name__ == "__main__":
    exit(main())
