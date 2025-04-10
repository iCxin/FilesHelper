# FilesHelper | 文件整理助手

[中文](#chinese) | [English](#english)

<a id="chinese"></a>
# 文件整理助手

一个帮助您自动整理文件的工具，支持自定义规则、图形界面、实时日志显示和自动创建目标文件夹。

## 功能特点

- 📁 自定义规则管理
  - 规则组支持
  - 规则包导入导出
  - 扩展名匹配
  - 关键词匹配
- 🎯 文件整理
  - 移动/复制模式
  - 自动创建文件夹
  - 进度跟踪
  - 操作统计
- 📊 日志系统
  - 实时操作日志
  - 日志保留设置
  - 每日日志轮转
  - 自动清理
- 💼 规则包系统
  - 版本控制
  - 格式验证
  - 合并支持
  - 备份与恢复
- 🗑️ 批量删除
  - 空目录清理
  - 空文件清理
  - 递归处理
  - 安全确认
- 🔄 目录合并
  - 相同父子目录合并
  - 自动清理空目录
  - 递归处理支持

## 系统要求

- Windows 7/8/10/11
- 无需Python环境

## 快速开始

1. 下载最新版本
2. 双击可执行文件
3. 添加整理规则
4. 选择源目录和目标目录
5. 开始整理

## 开发说明

### 环境要求
- Python 3.8+
- tkinter
- PyInstaller 6.3.0+

### 构建方法
```bash
# 安装依赖
pip install -r requirements.txt

# 构建可执行文件
python build.py
```

## 文档

详细文档请访问我们的 [Wiki](https://github.com/yourusername/fileshelper/wiki)。

## 更新日志

### 2025年4月10日
- 新增批量删除功能，支持删除空目录和空文件
- 优化规则组管理界面，提高用户体验
- 修复规则修改功能中的问题
- 改进日志显示和记录机制
- 优化整体界面布局和响应速度

## 许可证

版权所有 © 2024-2025 cxin 

---

<a id="english"></a>
# FilesHelper

A professional file organization tool with a modern graphical interface, supporting custom rules, real-time logging, and rule package management.

## Features

- 📁 Custom Rule Management
  - Rule groups support
  - Rule package import/export
  - Extension-based matching
  - Keyword-based matching
- 🎯 File Organization
  - Move/Copy modes
  - Automatic folder creation
  - Progress tracking
  - Operation statistics
- 📊 Logging System
  - Real-time operation logs
  - Log retention settings
  - Daily log rotation
  - Automatic cleanup
- 💼 Rule Package System
  - Version control
  - Format validation
  - Merge support
  - Backup & restore
- 🗑️ Batch Delete
  - Empty directory cleanup
  - Empty file cleanup
  - Recursive processing
  - Safety confirmation
- 🔄 Directory Merge
  - Same parent-child directory merge
  - Automatic empty directory cleanup
  - Recursive processing support

## System Requirements

- Windows 7/8/10/11
- No Python environment required

## Quick Start

1. Download the latest release
2. Double-click the executable file
3. Add organization rules
4. Select source and target directories
5. Start organizing

## Development

### Requirements
- Python 3.8+
- tkinter
- PyInstaller 6.3.0+

### Build
```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
python build.py
```

## Documentation

For detailed documentation, please visit our [Wiki](https://github.com/yourusername/fileshelper/wiki).

## Changelog

### April 10, 2025
- Added batch delete feature for empty directories and files
- Optimized rule group management interface
- Fixed rule modification functionality
- Improved log display and recording mechanism
- Enhanced overall UI layout and response speed

## License

© 2024-2025 cxin. All rights reserved. 