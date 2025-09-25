#!/usr/bin/env python3
"""
独立测试文件名格式化功能（不依赖ComfyUI）
"""

import os
import re
import tempfile
import datetime
import unicodedata
from pathlib import Path

try:
    from pypinyin import lazy_pinyin, Style
    HAS_PYPINYIN = True
    print("✅ pypinyin库可用，中文将转换为拼音")
except ImportError:
    HAS_PYPINYIN = False
    print("⚠️  pypinyin库不可用，中文将被移除")


def clean_filename(filename: str, use_chinese_conversion: bool = True) -> str:
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
    max_name_length = 50  # 测试用较短长度
    if len(cleaned_name) > max_name_length:
        cleaned_name = cleaned_name[:max_name_length].rstrip('_')

    return cleaned_name + ext.lower()  # 扩展名小写


def generate_timestamp_filename(original_path: str, cleaned_filename: str,
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


def create_test_files():
    """创建测试文件"""
    test_dir = tempfile.mkdtemp()
    print(f"创建测试目录: {test_dir}")

    # 创建各种问题文件名
    test_filenames = [
        "我的图片😊.JPG",
        "special@#$%characters.png",
        "   spaces   around   .txt",
        "中文文件名.pdf",
        "emoji🌟file✨.doc",
        "normal_file.mp4",
        "FILE WITH SPACES.AVI",
        "特殊符号！@#￥%……&*（）.jpg",
        "very___long____underscores.png",
        "MiXeD_CaSe_FiLe.TXT"
    ]

    # 创建文件
    for filename in test_filenames:
        try:
            file_path = os.path.join(test_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("test content")
        except Exception as e:
            print(f"创建文件失败 {filename}: {e}")

    return test_dir


def test_formatter():
    """测试格式化功能"""
    # 创建测试文件
    test_dir = create_test_files()

    print("\n" + "="*50)
    print("文件名格式化测试")
    print("="*50)

    print("\n原始文件列表:")
    original_files = os.listdir(test_dir)
    for i, filename in enumerate(original_files, 1):
        print(f"{i:2d}. {filename}")

    print(f"\n处理结果:")
    print("-" * 70)
    print(f"{'序号':<4} {'原始文件名':<25} {'格式化后':<25}")
    print("-" * 70)

    for i, filename in enumerate(original_files, 1):
        file_path = os.path.join(test_dir, filename)

        # 清理文件名
        cleaned = clean_filename(filename, use_chinese_conversion=True)

        # 生成最终文件名
        final = generate_timestamp_filename(file_path, cleaned, "file", use_timestamp=True)

        print(f"{i:2d}.  {filename:<25} -> {final:<25}")

    # 清理测试文件
    import shutil
    shutil.rmtree(test_dir)
    print(f"\n✅ 测试完成，已清理临时目录")


if __name__ == "__main__":
    test_formatter()