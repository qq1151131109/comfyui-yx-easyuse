# ComfyUI YX EasyUse 插件安装指南

## 📦 安装步骤

### 方法1: 直接克隆（推荐）
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/qq1151131109/comfyui-yx-easyuse.git
cd comfyui-yx-easyuse
pip install -r requirements.txt
```

### 方法2: 通过ComfyUI Manager
1. 在ComfyUI界面中，点击 Manager 按钮
2. 搜索 "YX EasyUse" 或 "filename formatter"
3. 点击安装

## 🚀 使用方法

### 1. 重启ComfyUI
安装完成后，重启ComfyUI以加载新插件。

### 2. 添加节点
在ComfyUI界面中：
1. 右键点击空白处
2. 选择 `Add Node` > `YX剪辑` > `文件名格式化工具`

### 3. 配置参数
- **folder_path**: 输入要处理的文件夹路径
  - 绝对路径：`/Users/username/Documents/files`
  - 相对路径：`test_files_formatting`（相对于ComfyUI/input目录）
- **prefix**: 文件名前缀（默认：`file`）
- **use_timestamp**: 是否添加时间戳（推荐：`True`）
- **use_chinese_conversion**: 中文转拼音（推荐：`True`）
- **recursive**: 是否处理子目录（默认：`False`）
- **dry_run**: 预览模式（首次使用推荐：`True`）

### 4. 测试示例

#### 准备测试文件
```bash
cd ComfyUI/input
mkdir test_files_formatting
cd test_files_formatting

# 创建测试文件
touch "我的图片😊.jpg"
touch "special@#$%file.png"
touch "   spaces   .txt"
touch "正常文件名.pdf"
touch "emoji🌟file✨test.doc"
```

#### 运行格式化
1. 在ComfyUI中添加 "文件名格式化工具" 节点
2. 设置 `folder_path` 为 `test_files_formatting`
3. 保持 `dry_run` 为 `True`（预览模式）
4. 点击 `Queue Prompt` 执行

#### 预期结果
```
原始文件名 -> 格式化后文件名
我的图片😊.jpg -> file_20240925_143022_wodetupian.jpg
special@#$%file.png -> file_20240925_143025_special_file.png
   spaces   .txt -> file_20240925_143028_spaces.txt
正常文件名.pdf -> file_20240925_143031_zhengchangwenjianming.pdf
emoji🌟file✨test.doc -> file_20240925_143034_emojifiletest.doc
```

## ⚙️ 参数详解

### folder_path（文件夹路径）
- **绝对路径示例**：`/Users/username/Downloads/messy_files`
- **相对路径示例**：`my_files`（相对于ComfyUI/input目录）
- **支持**：本地路径，网络路径（如果系统支持）

### prefix（前缀）
- **默认值**：`file`
- **示例**：设置为`img`，输出为`img_20240925_143022_filename.jpg`
- **建议**：使用有意义的前缀，如`photo`、`doc`、`video`等

### use_timestamp（时间戳）
- **格式**：`YYYYMMDD_HHMMSS`
- **基于**：文件的最后修改时间
- **优势**：确保文件名唯一，便于按时间排序

### use_chinese_conversion（中文转换）
- **需要**：pypinyin库支持
- **效果**：`中文.txt` → `zhongwen.txt`
- **回退**：如果没有pypinyin，中文字符将被移除

### recursive（递归处理）
- **True**：处理所有子目录中的文件
- **False**：只处理指定目录中的文件
- **注意**：大目录树可能需要较长时间

### dry_run（预览模式）
- **True**：只显示预览，不实际重命名
- **False**：执行实际的文件重命名
- **建议**：首次使用先预览确认结果

## 🔧 故障排除

### 问题1：找不到节点
**解决方法**：
1. 确认插件安装在 `ComfyUI/custom_nodes/comfyui-yx-easyuse/`
2. 重启ComfyUI
3. 检查控制台是否有错误信息

### 问题2：中文不转换为拼音
**原因**：缺少pypinyin库
**解决方法**：
```bash
pip install pypinyin
```

### 问题3：路径不存在错误
**检查**：
- 绝对路径是否正确
- 相对路径是否存在于ComfyUI/input目录下
- 路径权限是否正确

### 问题4：处理速度慢
**优化建议**：
- 先用小批量文件测试
- 避免处理过大的目录树
- 使用SSD存储提高I/O速度

## 📝 使用技巧

### 1. 批量处理工作流
```
1. 备份原始文件
2. 先用dry_run=True预览
3. 确认无误后设置dry_run=False执行
4. 验证结果
```

### 2. 不同场景的参数组合
```
# 处理下载文件
prefix: "download"
use_timestamp: True
recursive: False

# 整理照片
prefix: "photo"
use_timestamp: True
recursive: True

# 清理文档
prefix: "doc"
use_timestamp: False  # 如果不需要时间戳
recursive: True
```

### 3. 安全建议
- 重要文件务必备份
- 先用测试文件夹验证
- 大批量操作前分批处理

## 🔄 更新插件
```bash
cd ComfyUI/custom_nodes/comfyui-yx-easyuse
git pull origin main
pip install -r requirements.txt
```

重启ComfyUI完成更新。