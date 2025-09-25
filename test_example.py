#!/usr/bin/env python3
"""
文件名格式化工具测试示例
"""

import os
import tempfile
from nodes.filename_formatter import FilenameFormatterNode


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
        file_path = os.path.join(test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("test content")

    return test_dir


def test_formatter():
    """测试格式化功能"""
    # 创建测试文件
    test_dir = create_test_files()

    # 创建格式化节点
    formatter = FilenameFormatterNode()

    print("\n=== 测试开始 ===")
    print("原始文件列表:")
    for filename in os.listdir(test_dir):
        print(f"  - {filename}")

    # 执行格式化（预览模式）
    result_message, output_folder = formatter.format_filenames(
        folder_path=test_dir,
        prefix="test",
        use_timestamp=True,
        use_chinese_conversion=True,
        recursive=False,
        dry_run=True  # 预览模式
    )

    print("\n=== 格式化结果（预览） ===")
    print(result_message)

    # 清理测试文件
    import shutil
    shutil.rmtree(test_dir)
    print(f"\n清理测试目录: {test_dir}")


if __name__ == "__main__":
    test_formatter()