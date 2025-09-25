#!/usr/bin/env python3
"""
测试简化后的文件名格式化功能
"""

import os
import sys
import tempfile
import shutil

# 添加当前目录到路径，以便导入模块
sys.path.append(os.path.dirname(__file__))

# 创建模拟的folder_paths模块
class MockFolderPaths:
    @staticmethod
    def get_input_directory():
        return "/tmp/test_input"

# 替换导入
sys.modules['folder_paths'] = MockFolderPaths()

from nodes.filename_formatter import FilenameFormatterNode


def test_simple_formatter():
    """测试简化后的格式化功能"""
    # 创建测试目录结构
    test_root = tempfile.mkdtemp()
    test_input = os.path.join(test_root, "test_input")
    test_files_dir = os.path.join(test_input, "test_files")
    test_sub_dir = os.path.join(test_files_dir, "sub_folder")

    os.makedirs(test_files_dir, exist_ok=True)
    os.makedirs(test_sub_dir, exist_ok=True)

    print(f"创建测试目录: {test_root}")

    # 创建各种问题文件名
    test_files = {
        test_files_dir: [
            "我的图片😊.JPG",
            "special@#$%characters.png",
            "   spaces   around   .txt",
            "中文文件名.pdf",
            "emoji🌟file✨.doc",
            "normal_file.mp4"
        ],
        test_sub_dir: [
            "子目录文件.txt",
            "sub_emoji🎉.jpg"
        ]
    }

    # 创建文件
    for directory, filenames in test_files.items():
        for filename in filenames:
            try:
                file_path = os.path.join(directory, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("test content")
                print(f"创建文件: {filename}")
            except Exception as e:
                print(f"创建文件失败 {filename}: {e}")

    # 模拟folder_paths
    MockFolderPaths.get_input_directory = staticmethod(lambda: test_input)

    # 创建格式化节点并测试
    formatter = FilenameFormatterNode()

    print("\n" + "="*60)
    print("简化插件测试 - 只有两个参数")
    print("="*60)

    try:
        # 测试相对路径
        output_folder, result_message = formatter.format_filenames(
            folder_path="test_files",
            prefix="demo"
        )

        print(f"\n输出目录: {output_folder}")
        print(f"\n处理结果:")
        print(result_message)

        print(f"\n处理后的文件列表:")
        for root, dirs, files in os.walk(test_files_dir):
            level = root.replace(test_files_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 清理测试文件
    shutil.rmtree(test_root)
    print(f"\n✅ 测试完成，已清理临时目录")


if __name__ == "__main__":
    test_simple_formatter()