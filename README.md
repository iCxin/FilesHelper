# 文件整理助手

一个帮助用户自动整理文件的工具。

## 功能特点

- 支持自定义规则
- 图形化界面
- 实时日志显示
- 自动创建目标文件夹

## 开发环境要求

- Python 3.8+
- tkinter
- PyInstaller 6.3.0+

## 打包说明

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行打包脚本：
```bash
python build.py
```

3. 打包完成后，可执行文件将生成在 `dist` 目录下。

## 使用说明

1. 双击运行生成的exe文件
2. 在"规则管理"标签页添加整理规则
3. 在"文件整理"标签页选择要整理的文件夹
4. 点击"开始整理"按钮

## 开发者信息

- 开发者：cxin
- 邮箱：tojx@qq.com
- 个人网站：www.cxin.net

## 更新日志

### v1.7.0 (2025-04-10)
- 新增：规则包格式升级，添加版本和类型标识
- 新增：规则包格式验证功能
- 新增：规则包创建时间记录
- 优化：改进规则包导入导出功能
- 优化：增强错误提示信息

### v1.6.0 (2025-04-10)
- 新增：添加规则配置包功能
- 新增：支持导入导出规则包
- 新增：支持规则包合并功能
- 优化：改进按钮文字显示效果
- 优化：统一界面按钮样式

### v1.5.0 (2025-04-10)
- 新增：自动创建并保存日志到log目录
- 新增：支持设置日志保留天数
- 新增：日志文件按天自动轮转
- 新增：自动清理过期日志文件
- 优化：改进日志显示界面
- 优化：添加日志设置对话框

### v1.4.0 (2025-04-10)
- 新增：添加开发者信息显示
- 新增：添加个人网站链接
- 新增：优化界面布局和样式
- 新增：添加窗口位置记忆功能
- 新增：窗口默认居中显示
- 优化：改进按钮文字显示效果
- 优化：改进对话框显示效果

### v1.3.0 (2025-04-10)
- 新增：添加文件处理进度显示
- 新增：添加文件处理统计信息
- 优化：改进文件处理性能
- 优化：改进错误处理和提示

### v1.2.0 (2025-04-10)
- 新增：添加操作日志功能
- 新增：支持保存日志到文件
- 新增：支持清除日志
- 优化：改进用户界面交互

### v1.1.0 (2025-04-09)
- 新增：支持自定义目标文件夹名称
- 新增：支持文件扩展名匹配
- 优化：改进规则管理功能
- 优化：改进文件处理逻辑

### v1.0.0 (2025-04-09)
- 初始版本发布
- 基本文件分类功能
- 规则管理功能
- 文件移动和复制功能

## 使用方法

### 图形界面版本

1. 运行 `gui.py` 启动程序
2. 在"规则管理"选项卡中：
   - 添加分类规则
   - 导入规则包
   - 导出规则包
   - 删除规则
3. 在"文件整理"选项卡中选择源目录和目标目录
4. 选择操作模式（移动或复制）
5. 点击"开始整理"按钮
6. 在"操作日志"选项卡中查看处理结果
   - 可以保存当前日志到文件
   - 可以清除当前日志显示
   - 可以设置日志保留天数

### 规则配置包功能

- 规则包格式：JSON文件
- 规则包结构：
  ```json
  {
    "version": "1.0",
    "type": "file_organizer_rules",
    "created_at": "2025-04-31 12:00:00",
    "rules": {
      "关键词1": "文件夹1",
      "关键词2": "文件夹2"
    }
  }
  ```
- 规则包字段说明：
  - version: 规则包版本号
  - type: 规则包类型标识
  - created_at: 规则包创建时间
  - rules: 规则数据对象
- 导入规则包：
  - 自动验证规则包格式和内容
  - 可以选择覆盖或合并现有规则
  - 记录导入日志
- 导出规则包：
  - 导出当前所有规则
  - 自动添加版本和类型标识
  - 记录创建时间
  - 记录导出日志
- 规则包用途：
  - 快速添加常用规则
  - 在不同设备间同步规则
  - 备份和恢复规则配置
  - 分享规则配置给其他用户

### 日志功能说明

- 日志文件位置：程序运行目录下的`log`文件夹
- 日志文件命名：`file_organizer.log`
- 日志保留设置：
  - 默认保留最近7天的日志
  - 可通过"日志设置"按钮修改保留天数
  - 超过保留天数的日志文件会自动删除
- 日志内容：
  - 记录所有文件处理操作
  - 记录程序启动和关闭
  - 记录规则添加和删除
  - 记录错误和异常信息

### 命令行版本

1. 运行 `main.py` 启动程序
2. 按照提示选择操作：
   - 1: 添加分类规则
   - 2: 开始整理文件
   - 3: 查看当前规则
   - 4: 删除规则
   - 5: 关于
   - 6: 退出

## 系统要求

- Python 3.6 或更高版本
- 操作系统：Windows/macOS/Linux

## 安装依赖

```bash
pip install -r requirements.txt
```

## 许可证

© 2025 cxin. 保留所有权利。 