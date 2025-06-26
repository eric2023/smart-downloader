请分析当前项目并生成详细的项目指引文档。

分析要求：
1. 项目基本信息：项目名称、主要功能、技术栈
2. 构建体系：构建工具、依赖管理、编译配置
3. 模块划分：项目结构、核心模块、组件关系
4. 开发规范：代码风格、目录结构、命名约定
5. 部署说明：构建流程、部署方式、环境要求

请将分析结果输出到 .cursor/smart-downloader-guide.md 文件中，使用 Markdown 格式。# Smart Downloader

智能递归文件下载工具，能够自动分析目标服务器并选择最佳下载策略。

## 功能特性

- **🚀 智能CPU检测**：自动检测CPU核数，智能配置最优线程数（CPU核数×2）
- **⚙️ 零配置启动**：首次运行自动生成最优配置，支持热更新
- **📁 完整目录结构保持**：完美保持原始服务器目录层级，支持中文路径
- **🔍 智能服务器检测**：自动识别Apache、Nginx、SimpleHTTP等服务器类型
- **🎯 多策略下载**：支持wget、Python requests和混合策略
- **📥 递归下载**：自动遍历目录结构下载所有文件
- **⚡ 断点续传**：支持HTTP Range请求的文件断点续传
- **🔄 多线程下载**：智能并发下载，根据硬件自动优化
- **🎛️ 智能过滤**：支持文件类型、大小、路径模式过滤
- **📊 进度监控**：实时显示下载进度和统计信息
- **🛡️ 错误恢复**：自动重试和策略切换
- **📝 详细日志**：完整的操作日志和错误追踪

## 安装要求

### 系统要求
- Python 3.7+
- Linux/Unix系统（推荐）
- wget工具（可选，用于wget策略）

### Python依赖
```bash
pip install -r requirements.txt
```

主要依赖：
- `requests` - HTTP请求库
- `beautifulsoup4` - HTML解析
- `urllib3` - URL处理

## 快速开始

### 基本用法
```bash
# 分析目标网站结构
python3 smart_downloader.py --analyze http://example.com/files/

# 下载指定URL的所有文件
python3 smart_downloader.py --download http://example.com/files/

# 指定输出目录
python3 smart_downloader.py --download http://example.com/files/ --output ./downloads

# 强制使用特定策略
python3 smart_downloader.py --download http://example.com/files/ --strategy python

# 自定义线程数
python3 smart_downloader.py --download http://example.com/files/ --workers 16
```

### 多种执行方式
```bash
# 方式1：直接执行主程序
python3 smart_downloader.py --download http://example.com/files/

# 方式2：使用便捷脚本
python3 run.py --download http://example.com/files/

# 方式3：模块方式执行
python3 -m __main__ --download http://example.com/files/
```

### 高级选项
```bash
# 启用详细输出
python3 smart_downloader.py --download http://example.com/files/ --verbose

# 静默模式
python3 smart_downloader.py --download http://example.com/files/ --quiet

# 使用自定义配置文件
python3 smart_downloader.py --download http://example.com/files/ --config my_config.json

# 查看帮助信息
python3 smart_downloader.py --help
```

### Python API
```python
from smart_downloader import SmartDownloader

# 创建下载器实例
downloader = SmartDownloader()

# 分析服务器
analysis = downloader.analyze('http://example.com/files/')
if analysis['success']:
    print(f"服务器类型：{analysis['server_type']}")
    print(f"预估文件数：{analysis['estimated_files']}")

# 执行下载
result = downloader.download(
    url='http://example.com/files/',
    output_dir='./downloads',
    strategy='python'  # 可选：指定策略
)

# 检查结果
if result['success']:
    print(f"下载完成！使用策略：{result['strategy_used']}")
    print(f"输出目录：{result['output_dir']}")
else:
    print(f"下载失败：{result['error']}")
```

## 项目结构

```
download/
├── smart_downloader.py    # 主程序文件
├── run.py                # 便捷执行脚本
├── __main__.py           # 模块执行入口
├── __init__.py           # 包初始化文件
├── config.json           # 配置文件（自动生成）
├── requirements.txt      # Python依赖
├── LICENSE              # MIT许可证
├── README.md            # 项目文档
├── detectors/           # 服务器检测模块
│   ├── __init__.py
│   ├── server_detector.py
│   └── page_analyzer.py
├── downloaders/         # 下载策略模块
│   ├── __init__.py
│   ├── base_downloader.py
│   ├── wget_downloader.py
│   ├── python_downloader.py
│   └── hybrid_downloader.py
└── utils/              # 工具模块
    ├── __init__.py
    ├── config_manager.py
    ├── config_wrapper.py
    ├── logger.py
    ├── file_utils.py
    └── url_utils.py
```

## 配置系统

### 智能配置
首次运行时，工具会自动：
- 检测CPU核数并设置最优线程数
- 生成基于系统环境的配置文件
- 根据系统变化自动更新配置

### 配置文件示例
```json
{
  "download": {
    "max_workers": 32,           // 基于CPU核数自动设置
    "timeout": 30,               // 连接超时（秒）
    "retry_attempts": 3,         // 重试次数
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "overwrite_existing": true,  // 覆盖已存在文件
    "chunk_size": 8192,         // 下载块大小
    "delay_between_requests": 0.1,  // 请求间延迟
    "max_file_size": "1GB"      // 最大文件大小
  },
  "network": {
    "verify_ssl": true,         // SSL验证
    "connection_pool_size": 32  // 连接池大小
  },
  "filters": {
    "exclude_extensions": [],   // 排除的文件扩展名
    "include_extensions": [],   // 包含的文件扩展名
    "exclude_patterns": [],     // 排除的文件模式
    "max_depth": 10            // 最大递归深度
  },
  "output": {
    "preserve_timestamps": true, // 保留文件时间戳
    "create_index": true,       // 创建目录索引
    "log_level": "INFO",        // 日志级别
    "console_output": true      // 控制台输出
  }
}
```

### 配置优先级
1. 命令行参数（最高优先级）
2. 配置文件设置
3. 智能默认值（基于系统环境）

## 下载策略

### 1. Python策略（推荐）
- **适用场景**：通用场景，复杂页面结构
- **优势**：跨平台、灵活可控、支持认证
- **特性**：智能多线程、完整错误处理
- **要求**：Python环境和依赖库

### 2. Wget策略
- **适用场景**：标准HTTP服务器、批量下载
- **优势**：成熟稳定、功能完整、速度快
- **特性**：原生递归、断点续传
- **要求**：系统已安装wget

### 3. 混合策略
- **适用场景**：未知服务器类型、自动优化
- **优势**：智能适应、自动降级、最佳性能
- **特性**：动态策略选择、故障转移
- **推荐**：作为备用选择

## 命令行参数

### 主要操作
- `--analyze URL` - 分析目标网站结构
- `--download URL` - 下载网站内容

### 可选参数
- `--output DIR, -o DIR` - 输出目录（默认：downloads）
- `--strategy {wget,python,hybrid}, -s` - 指定下载策略
- `--config FILE, -c FILE` - 配置文件路径
- `--workers NUM, -w NUM` - 指定线程数（覆盖配置文件）
- `--verbose, -v` - 启用详细日志输出
- `--quiet, -q` - 静默模式
- `--version` - 显示版本信息
- `--help` - 显示帮助信息

## 实际使用示例

### 成功案例
以下是实际测试过的下载场景：

```bash
# 下载Apache服务器文件列表
python3 smart_downloader.py --download http://10.20.33.88:8888/

# 结果：成功下载1637个文件，总大小约1GB
# 自动检测：Apache服务器，使用Python策略
# 智能配置：16核CPU，32线程并发
```

### 性能表现
- **CPU检测**：自动识别16核处理器
- **线程配置**：智能设置32个工作线程
- **下载效率**：平均速度根据网络环境自动优化
- **错误处理**：自动重试失败的文件

## 故障排除

### 常见问题

1. **配置文件问题**
   ```bash
   # 删除配置文件重新生成
   rm config.json
   python3 smart_downloader.py --analyze http://example.com/
   ```

2. **权限错误**
   ```bash
   # 确保输出目录有写权限
   chmod 755 /path/to/output/dir
   ```

3. **网络连接问题**
   - 检查防火墙设置
   - 验证URL可访问性
   - 增加超时时间：`--workers 8`

4. **内存不足**
   - 减少线程数：`--workers 4`
   - 设置文件大小限制
   - 使用wget策略：`--strategy wget`

### 调试模式
```bash
# 启用详细日志
python3 smart_downloader.py --download http://example.com/ --verbose

# 查看日志文件
tail -f smart_downloader.log

# 分析模式（不下载）
python3 smart_downloader.py --analyze http://example.com/
```

## 性能优化

### 自动优化功能
- **智能线程数**：基于CPU核数自动设置
- **连接池优化**：动态调整连接池大小
- **内存管理**：流式下载，避免内存溢出
- **网络优化**：智能重试和超时设置

### 手动调优建议
1. **线程数设置**：通常CPU核数×2为最优
2. **网络环境**：网络较慢时减少并发数
3. **存储性能**：SSD存储可以使用更多线程
4. **目标服务器**：根据服务器负载能力调整

### 性能监控
```bash
# 查看实时下载状态
python3 smart_downloader.py --download http://example.com/ --verbose

# 监控系统资源
htop  # 查看CPU和内存使用
iotop # 查看磁盘I/O
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
git clone <repository>
cd smart-downloader
pip install -r requirements.txt
python3 smart_downloader.py --help
```

## 更新日志

### v1.0.0 (2025-06-26)
- ✨ 智能CPU检测和线程配置
- ✨ 零配置启动，自动生成最优配置
- ✨ 完整目录结构保持，支持中文路径
- ✨ 多种执行方式支持
- ✨ 增强的错误处理和日志系统
- ✨ 配置热更新和系统适配
- 🔧 统一项目结构，消除代码重复
- 🔧 完善的命令行接口
- 📚 完整的文档和使用示例

---

**Smart Downloader** - 让文件下载变得智能而简单！ 