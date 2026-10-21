<div align="right"><sub><code>iCxin / FilesHelper</code></sub></div>

# FilesHelper

> Windows 上的文件整理工具：按自定义规则把源目录里的文件移动或复制到目标目录。
> A Windows file organizer: move or copy a source directory into target folders by your own rules.

| | |
|:--|:--|
| **状态** | 维护中 |
| **栈** | `Python` · `tkinter` · `PyInstaller` |
| **平台** | Windows 7 / 8 / 10 / 11 |
| **许可** | 保留所有权利 |

---

## 01 · 这是什么

带图形界面的文件整理助手。先定义规则（按扩展名或关键词匹配），再指定源目录与目标目录，按移动或复制执行；过程中显示进度与操作统计，并写入日志。发布形式是 PyInstaller 打包的可执行文件，使用者不需要安装 Python。

## 02 · 特性

| 能力 | 说明 |
|:--|:--|
| 规则管理 | 规则组分组管理，规则包可导入导出 |
| 匹配方式 | 扩展名匹配、关键词匹配 |
| 整理模式 | 移动或复制，自动创建目标文件夹 |
| 进度与统计 | 实时进度显示、操作统计 |
| 日志系统 | 实时操作日志，可设保留时长，每日轮转，自动清理 |
| 规则包 | 版本控制、格式校验、合并、备份与恢复 |
| 批量删除 | 删除空目录与空文件，递归处理，执行前确认 |
| 目录合并 | 合并相同父子目录，合并后自动清理空目录 |

## 03 · 快速开始

1. 下载最新发布的可执行文件
2. 双击运行
3. 添加整理规则
4. 选择源目录与目标目录
5. 开始整理

无需 Python 环境。

## 04 · 从源码构建

环境要求：Python 3.8+、tkinter、PyInstaller 6.3.0+。

```bash
pip install -r requirements.txt
```

打包脚本为 `build.py`：

```bash
python build.py
```

## 05 · 更新日志

2025-04-10：

- 新增批量删除，支持删除空目录与空文件
- 优化规则组管理界面
- 修复规则修改功能中的问题
- 改进日志显示与记录机制
- 调整整体界面布局与响应速度

## 06 · 许可

版权所有 © 2024-2025 cxin，保留所有权利。仓库未提供开源许可证。

---

<div align="right"><sub>从像素到混凝土 · <a href="https://github.com/iCxin">iCxin</a></sub></div>
