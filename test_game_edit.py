#!/usr/bin/env python3
"""
游戏视频自动剪辑节点测试脚本
"""

import os
import sys
import tempfile
import cv2
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加当前目录到路径，以便导入模块
sys.path.append(os.path.dirname(__file__))

# 创建模拟的ComfyUI环境
class MockFolderPaths:
    @staticmethod
    def get_input_directory():
        return "/tmp/test_input"

    @staticmethod
    def get_output_directory():
        return "/tmp/test_output"

# 替换导入
sys.modules['folder_paths'] = MockFolderPaths()

def create_test_game_video(output_path, duration=8, fps=30):
    """创建测试游戏视频"""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = int(duration * fps)
    logger.info(f"创建测试游戏视频: {output_path} ({duration}s, {total_frames}帧)")

    for frame_num in range(total_frames):
        # 创建基础背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (30, 30, 30)  # 深灰色游戏背景

        time_sec = frame_num / fps

        # 模拟游戏场景：前2秒有操作，2-6秒停顿思考，6-8秒继续操作
        if time_sec < 2 or time_sec > 6:
            # 有操作时段：模拟消消乐游戏

            # 绘制游戏棋盘
            for row in range(8):
                for col in range(8):
                    x = 50 + col * 60
                    y = 50 + row * 50

                    # 根据时间变化颜色模拟消除效果
                    color_shift = int(time_sec * 50 + frame_num * 5) % 255
                    color = ((color_shift + row * 30) % 255,
                           (color_shift + col * 40) % 255,
                           (color_shift + row * col * 10) % 255)

                    cv2.rectangle(frame, (x, y), (x+50, y+40), color, -1)
                    cv2.rectangle(frame, (x, y), (x+50, y+40), (255, 255, 255), 1)

            # 绘制分数
            score = int(time_sec * 1000 + frame_num * 10)
            cv2.putText(frame, f"Score: {score}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            # 添加粒子特效模拟消除动画
            for i in range(5):
                particle_x = int(200 + np.sin(frame_num * 0.1 + i) * 100)
                particle_y = int(200 + np.cos(frame_num * 0.1 + i) * 100)
                cv2.circle(frame, (particle_x, particle_y), 3, (255, 255, 255), -1)

        else:
            # 静止思考时段：只有静态界面

            # 静态棋盘
            for row in range(8):
                for col in range(8):
                    x = 50 + col * 60
                    y = 50 + row * 50
                    color = (100, 150, 200)  # 静态蓝色
                    cv2.rectangle(frame, (x, y), (x+50, y+40), color, -1)
                    cv2.rectangle(frame, (x, y), (x+50, y+40), (255, 255, 255), 1)

            # 静态分数（停顿时分数不变）
            cv2.putText(frame, f"Score: 2000", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            # 显示思考状态
            cv2.putText(frame, "THINKING...", (width//2-80, height-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)

        out.write(frame)

    out.release()
    logger.info(f"测试游戏视频创建完成: {output_path}")

def test_game_video_edit():
    """测试游戏视频剪辑功能"""
    from nodes.game_video_auto_edit import GameVideoAutoEditNode

    # 创建测试目录
    test_input_dir = tempfile.mkdtemp(prefix="game_test_input_")
    test_output_dir = tempfile.mkdtemp(prefix="game_test_output_")

    logger.info(f"测试输入目录: {test_input_dir}")
    logger.info(f"测试输出目录: {test_output_dir}")

    try:
        # 创建测试游戏视频
        test_videos = [
            ("match3_game.mp4", 8),
            ("puzzle_game.mp4", 10),
        ]

        for filename, duration in test_videos:
            video_path = os.path.join(test_input_dir, filename)
            create_test_game_video(video_path, duration=duration, fps=30)

        # 模拟folder_paths
        MockFolderPaths.get_input_directory = staticmethod(lambda: os.path.dirname(test_input_dir))
        MockFolderPaths.get_output_directory = staticmethod(lambda: test_output_dir)

        # 创建节点实例
        node = GameVideoAutoEditNode()

        logger.info("开始测试游戏视频自动剪辑节点...")

        # 测试预览模式
        logger.info("=== 测试预览模式 ===")
        output_path, analysis_summary = node.auto_edit_videos(
            input_folder=os.path.basename(test_input_dir),
            output_folder_prefix="game_preview",
            idle_threshold=0.015,
            min_segment_duration=2.0,
            pixel_threshold=40,
            preserve_buffer=1.0,
            enable_preview=True
        )

        print("\n🔍 预览模式分析结果:")
        print("=" * 70)
        print(analysis_summary)
        print("=" * 70)

        # 测试实际剪辑
        logger.info("=== 测试剪辑模式 ===")
        output_path, analysis_summary = node.auto_edit_videos(
            input_folder=os.path.basename(test_input_dir),
            output_folder_prefix="game_edit",
            idle_threshold=0.020,
            min_segment_duration=3.0,
            pixel_threshold=35,
            preserve_buffer=0.5,
            enable_preview=False
        )

        print("\n✂️ 剪辑模式结果:")
        print("=" * 70)
        print(f"输出路径: {output_path}")
        print(analysis_summary)
        print("=" * 70)

        # 检查输出文件
        if output_path and os.path.exists(output_path):
            output_files = [f for f in os.listdir(output_path) if f.endswith('.mp4')]
            logger.info(f"生成的剪辑文件: {output_files}")

            for file in output_files:
                file_path = os.path.join(output_path, file)
                file_size = os.path.getsize(file_path)

                # 检查视频信息
                cap = cv2.VideoCapture(file_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                cap.release()

                logger.info(f"  {file}: {file_size} bytes, {duration:.1f}s")

        logger.info("✅ 游戏视频自动剪辑测试完成")

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理测试文件
        import shutil
        try:
            shutil.rmtree(test_input_dir)
            if os.path.exists(test_output_dir):
                shutil.rmtree(test_output_dir)
            logger.info("测试文件已清理")
        except:
            pass

def test_node_import():
    """测试节点导入"""
    try:
        from nodes.game_video_auto_edit import GameVideoAutoEditNode, NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

        logger.info("✅ 节点导入成功")
        logger.info(f"节点类: {list(NODE_CLASS_MAPPINGS.keys())}")
        logger.info(f"显示名称: {list(NODE_DISPLAY_NAME_MAPPINGS.values())}")

        # 测试节点实例化
        node = GameVideoAutoEditNode()
        input_types = node.INPUT_TYPES()

        logger.info("节点参数:")
        for param_type, params in input_types.items():
            logger.info(f"  {param_type}: {list(params.keys())}")

        return True
    except Exception as e:
        logger.error(f"❌ 节点导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎮 游戏视频自动剪辑节点测试")
    print("=" * 50)

    # 测试导入
    if test_node_import():
        logger.info("节点导入测试通过，开始功能测试...")
        test_game_video_edit()
    else:
        logger.error("节点导入测试失败，跳过功能测试")