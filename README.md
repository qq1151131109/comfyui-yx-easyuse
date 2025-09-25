# ComfyUI YX EasyUse Plugin

一个专注于文件处理和工作流优化的ComfyUI插件集合。

## 功能特性

### 文件名格式化工具
- 🔧 **智能文件名清理**: 自动处理中文、特殊字符、emoji等问题字符
- 📅 **时间戳集成**: 基于文件修改时间添加时间戳
- 🌏 **中文转拼音**: 支持将中文字符转换为拼音（可选）
- 📁 **批量处理**: 支持单目录或递归处理子目录
- 🔍 **预览模式**: 支持干跑模式，预览重命名结果
- ⚡ **智能去重**: 自动处理文件名冲突，添加序号

## 安装方法

### 方法1: 使用ComfyUI Manager（推荐）
1. 在ComfyUI中安装ComfyUI Manager
2. 在Manager中搜索 "YX EasyUse"
3. 点击安装

### 方法2: 手动安装
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1151131109/comfyui-yx-easyuse.git
cd comfyui-yx-easyuse
pip install -r requirements.txt
```

## 依赖库

### 必需依赖
- `unicodedata` (Python内置)
- `pathlib` (Python内置)

### 可选依赖
```bash
pip install pypinyin  # 用于中文转拼音功能
```

## 使用说明

### 文件名格式化工具

1. **基本用法**:
   - 在ComfyUI界面中添加 "文件名格式化工具" 节点
   - 输入要处理的文件夹路径（绝对路径或相对于input目录的路径）
   - 设置文件名前缀
   - 点击执行

2. **参数说明**:
   - `folder_path`: 目标文件夹路径
   - `prefix`: 新文件名前缀（默认: "file"）
   - `use_timestamp`: 是否添加时间戳（默认: True）
   - `use_chinese_conversion`: 是否转换中文为拼音（默认: True）
   - `recursive`: 是否递归处理子目录（默认: False）
   - `dry_run`: 预览模式，不实际重命名（默认: True）

3. **输出格式**:
   ```
   原文件名: 我的图片😊.JPG
   新文件名: file_20241225_143022_wodetupiaoer.jpg

   原文件名: special@#$%characters.png
   新文件名: file_20241225_143025_special_characters.png
   ```

## 特性详解

### 文件名清理规则
1. **中文处理**: 转换为拼音或移除
2. **Emoji移除**: 自动识别并移除emoji符号
3. **特殊字符**: 替换为下划线
4. **空格处理**: 转换为下划线
5. **连续下划线**: 合并为单个下划线
6. **扩展名**: 统一转换为小写

### 时间戳格式
- 格式: `YYYYMMDD_HHMMSS`
- 基于文件的最后修改时间
- 例子: `20241225_143022`

### 防重命名机制
- 自动检测文件名冲突
- 添加三位数序号: `_001`, `_002`, `_003`...
- 最大支持9999个重复文件

## 常见问题

### Q: 中文转换不生效？
A: 请确保安装了pypinyin库: `pip install pypinyin`

### Q: 处理大量文件很慢？
A: 建议先用预览模式检查结果，确认无误后再执行实际重命名

### Q: 支持哪些文件格式？
A: 支持所有文件格式，主要处理文件名而不是文件内容

### Q: 可以恢复重命名吗？
A: 建议处理前备份重要文件，插件本身不提供撤销功能

## 更新日志

### v1.0.0
- ✨ 初始发布
- 🔧 文件名格式化工具
- 📅 时间戳支持
- 🌏 中文转拼音支持
- 📁 递归目录处理
- 🔍 预览模式

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [qq1151131109](https://github.com/qq1151131109)
- 项目地址: https://github.com/qq1151131109/comfyui-yx-easyuse