"""
文件名格式化节点
将文件夹中所有文件名格式化为程序友好的英文+数字格式，包含时间戳
"""

import os
import re
import unicodedata
import datetime
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

import folder_paths


class FilenameFormatterNode:
    """文件名格式化节点"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {
                    "default": "",
                    "tooltip": "要格式化文件名的文件夹路径（绝对路径或相对路径）"
                }),
                "prefix": ("STRING", {
                    "default": "file",
                    "tooltip": "新文件名的前缀"
                }),
                "use_timestamp": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否在文件名中包含时间戳"
                }),
                "use_chinese_conversion": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否将中文转换为拼音（需要安装pypinyin库）"
                }),
                "recursive": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否递归处理子目录"
                }),
                "dry_run": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "仅预览，不实际重命名文件"
                })
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("result_message", "output_folder")
    FUNCTION = "format_filenames"
    CATEGORY = "YX剪辑"

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.rename_map = []

    def clean_filename(self, filename: str, use_chinese_conversion: bool = True) -> str:
        """
        清理文件名，移除特殊字符和emoji，转换中文
        """
        # 分离文件名和扩展名
        name_part, ext = os.path.splitext(filename)

        # 处理中文字符
        if use_chinese_conversion and HAS_PYPINYIN:
            # 使用pypinyin转换中文为拼音
            cleaned_name = ""
            for char in name_part:
                if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                    pinyin = lazy_pinyin(char, style=Style.NORMAL)[0]
                    cleaned_name += pinyin
                else:
                    cleaned_name += char
        else:
            # 不转换中文，直接移除或替换
            cleaned_name = name_part

        # 移除或替换特殊字符和emoji
        # 1. 移除emoji和其他符号
        cleaned_name = ''.join(char for char in cleaned_name
                              if unicodedata.category(char) not in ['So', 'Sm', 'Sk', 'Sc'])

        # 2. 移除控制字符
        cleaned_name = ''.join(char for char in cleaned_name
                              if unicodedata.category(char) not in ['Cc', 'Cf'])

        # 3. 替换空格和其他分隔符为下划线
        cleaned_name = re.sub(r'[\s\-\+\=\[\]\(\)\{\}\|\\\/:;"\'<>,\?!\*\&\%\$\#@\~`]+', '_', cleaned_name)

        # 4. 移除非ASCII字符（如果没有转换中文）
        if not (use_chinese_conversion and HAS_PYPINYIN):
            cleaned_name = re.sub(r'[^\x00-\x7F]+', '_', cleaned_name)

        # 5. 合并多个连续的下划线
        cleaned_name = re.sub(r'_+', '_', cleaned_name)

        # 6. 移除开头和结尾的下划线
        cleaned_name = cleaned_name.strip('_')

        # 7. 确保文件名不为空
        if not cleaned_name:
            cleaned_name = "unnamed"

        # 8. 限制长度（保留扩展名空间）
        max_name_length = 200  # 留一些空间给时间戳和序号
        if len(cleaned_name) > max_name_length:
            cleaned_name = cleaned_name[:max_name_length].rstrip('_')

        return cleaned_name + ext.lower()  # 扩展名小写

    def generate_timestamp_filename(self, original_path: str, cleaned_filename: str,
                                   prefix: str, use_timestamp: bool) -> str:
        """
        生成包含时间戳的最终文件名
        """
        # 获取文件修改时间
        stat = os.stat(original_path)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)

        # 分离文件名和扩展名
        name_part, ext = os.path.splitext(cleaned_filename)

        # 构建新文件名
        parts = [prefix] if prefix else []

        if use_timestamp:
            timestamp = mtime.strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        if name_part and name_part != "unnamed":
            parts.append(name_part)

        new_name = "_".join(parts) + ext
        return new_name

    def get_unique_filename(self, directory: str, desired_name: str) -> str:
        """
        确保文件名唯一，如果存在重复则添加序号
        """
        name_part, ext = os.path.splitext(desired_name)
        counter = 1
        final_name = desired_name

        while os.path.exists(os.path.join(directory, final_name)):
            final_name = f"{name_part}_{counter:03d}{ext}"
            counter += 1

            # 防止无限循环
            if counter > 9999:
                break

        return final_name

    def process_directory(self, folder_path: str, prefix: str, use_timestamp: bool,
                         use_chinese_conversion: bool, recursive: bool, dry_run: bool) -> List[Tuple[str, str]]:
        """
        处理目录中的所有文件
        """
        rename_operations = []

        if not os.path.exists(folder_path):
            raise ValueError(f"目录不存在: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是目录: {folder_path}")

        # 获取文件列表
        if recursive:
            file_paths = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
        else:
            file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                         if os.path.isfile(os.path.join(folder_path, f))]

        # 处理每个文件
        for file_path in file_paths:
            try:
                directory = os.path.dirname(file_path)
                original_filename = os.path.basename(file_path)

                # 跳过隐藏文件
                if original_filename.startswith('.'):
                    continue

                # 清理文件名
                cleaned_filename = self.clean_filename(original_filename, use_chinese_conversion)

                # 生成时间戳文件名
                timestamped_filename = self.generate_timestamp_filename(
                    file_path, cleaned_filename, prefix, use_timestamp
                )

                # 确保文件名唯一
                final_filename = self.get_unique_filename(directory, timestamped_filename)

                # 检查是否需要重命名
                if original_filename != final_filename:
                    new_path = os.path.join(directory, final_filename)
                    rename_operations.append((file_path, new_path))

                    if not dry_run:
                        # 实际执行重命名
                        os.rename(file_path, new_path)
                        self.processed_count += 1

            except Exception as e:
                self.error_count += 1
                print(f"处理文件 {file_path} 时出错: {str(e)}")
                continue

        return rename_operations

    def format_filenames(self, folder_path: str, prefix: str, use_timestamp: bool,
                        use_chinese_conversion: bool, recursive: bool, dry_run: bool):
        """
        主处理函数
        """
        self.processed_count = 0
        self.error_count = 0
        self.rename_map = []

        try:
            # 解析路径
            if not os.path.isabs(folder_path):
                # 如果是相对路径，相对于ComfyUI的input目录
                input_dir = folder_paths.get_input_directory()
                folder_path = os.path.join(input_dir, folder_path)

            # 标准化路径
            folder_path = os.path.abspath(folder_path)

            # 处理文件
            rename_operations = self.process_directory(
                folder_path, prefix, use_timestamp, use_chinese_conversion, recursive, dry_run
            )

            self.rename_map = rename_operations

            # 生成结果信息
            mode = "预览模式" if dry_run else "执行模式"
            result_message = f"""
文件名格式化完成 - {mode}

处理目录: {folder_path}
预处理文件: {len(rename_operations)}个
{"实际重命名: " + str(self.processed_count) + "个" if not dry_run else ""}
错误: {self.error_count}个

重命名详情:
"""

            # 添加重命名详情（限制显示数量避免过长）
            display_limit = 20
            for i, (old_path, new_path) in enumerate(rename_operations[:display_limit]):
                old_name = os.path.basename(old_path)
                new_name = os.path.basename(new_path)
                result_message += f"\n{old_name} -> {new_name}"

            if len(rename_operations) > display_limit:
                result_message += f"\n... 还有 {len(rename_operations) - display_limit} 个文件"

            # 添加库依赖提示
            if use_chinese_conversion and not HAS_PYPINYIN:
                result_message += "\n\n注意: 未安装pypinyin库，中文字符将被移除而不是转换为拼音"
                result_message += "\n安装命令: pip install pypinyin"

            return (result_message, folder_path)

        except Exception as e:
            error_message = f"文件名格式化失败: {str(e)}"
            return (error_message, folder_path if 'folder_path' in locals() else "")


# 节点映射
NODE_CLASS_MAPPINGS = {
    "FilenameFormatterNode": FilenameFormatterNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FilenameFormatterNode": "文件名格式化工具"
}