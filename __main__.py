#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Downloader - 模块执行入口

支持使用 python -m smart_downloader 执行
"""

import sys
import os

# 确保能够导入当前包
if __name__ == "__main__":
    # 添加父目录到路径，确保能找到smart_downloader包
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # 导入并运行主函数
    from .smart_downloader import main
    sys.exit(main()) 