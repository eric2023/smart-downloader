#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Downloader - 直接执行脚本

这个脚本可以直接运行，提供便捷的执行方式
"""

import sys
import os

# 添加当前目录和父目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 确保能够导入smart_downloader包
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入并运行主函数
from smart_downloader import main

if __name__ == "__main__":
    sys.exit(main()) 