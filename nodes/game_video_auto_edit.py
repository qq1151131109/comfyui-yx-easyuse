import os
import glob
import cv2
import numpy as np
import tempfile
import logging
import uuid
import shutil
from pathlib import Path
import ffmpeg
import folder_paths
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置logger
logger = logging.getLogger(__name__)

def generate_unique_folder_name(prefix: str, output_dir: str) -> str:
    """生成唯一的文件夹名称"""
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"{prefix}_{unique_id}"

    while os.path.exists(os.path.join(output_dir, folder_name)):
        unique_id = str(uuid.uuid4())[:8]
        folder_name = f"{prefix}_{unique_id}"

    return folder_name

def resolve_path(path: str) -> str:
    """解析路径，支持相对路径和绝对路径"""
    if not path or not path.strip():
        return ""

    path = path.strip()

    if os.path.isabs(path):
        return path

    try:
        input_dir = folder_paths.get_input_directory()
        return os.path.join(input_dir, path)
    except:
        return os.path.abspath(path)

def create_sanitized_temp_folder(input_folder_path: str) -> tuple:
    """创建临时文件夹处理文件名问题"""
    temp_dir = tempfile.mkdtemp(prefix="sanitized_videos_")
    filename_mapping = {}

    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']

    for filename in os.listdir(input_folder_path):
        file_path = os.path.join(input_folder_path, filename)

        if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in video_extensions):
            # 简单的文件名清理
            sanitized_filename = filename
            temp_file_path = os.path.join(temp_dir, sanitized_filename)

            try:
                os.symlink(file_path, temp_file_path)
            except:
                shutil.copy2(file_path, temp_file_path)

            filename_mapping[filename] = sanitized_filename

    return temp_dir, str(filename_mapping)

def cleanup_temp_folder(temp_dir: str):
    """清理临时文件夹"""
    try:
        shutil.rmtree(temp_dir)
    except:
        pass

class GameVideoAutoEditNode:
    """
    游戏视频自动剪辑节点
    基于帧差检测自动识别游戏视频中的无操作片段并剪辑出精彩部分
    支持批量处理文件夹中的所有视频文件
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_folder": ("STRING", {"default": "", "tooltip": "输入视频文件夹路径（支持相对路径和绝对路径）"}),
                "output_folder_prefix": ("STRING", {"default": "game_auto_edit", "tooltip": "输出文件夹前缀"}),
                "idle_threshold": ("FLOAT", {"default": 0.015, "min": 0.005, "max": 0.1, "step": 0.005, "tooltip": "无操作检测阈值 (0.005-0.1，值越小越敏感)"}),
                "min_segment_duration": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 30.0, "step": 0.5, "tooltip": "最小无操作片段时长（秒），短于此时长的片段将被保留"}),
                "pixel_threshold": ("INT", {"default": 40, "min": 20, "max": 100, "step": 5, "tooltip": "像素差异阈值 (20-100，用于过滤鼠标移动等微小变化)"}),
            },
            "optional": {
                "preserve_buffer": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0, "step": 0.5, "tooltip": "保留缓冲时间（秒），在无操作片段前后保留的时间"}),
                "enable_preview": ("BOOLEAN", {"default": False, "tooltip": "启用预览模式（只分析不剪辑）"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output_path", "analysis_summary")
    FUNCTION = "auto_edit_videos"
    CATEGORY = "YX剪辑"

    def __init__(self):
        self.processed_count = 0
        self.total_idle_time_removed = 0.0
        self.analysis_results = []

    def detect_motion_simple(self, video_path, idle_threshold=0.015, pixel_threshold=40):
        """简化的运动检测算法"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None, None

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or total_frames <= 0:
            logger.error(f"视频参数异常: fps={fps}, frames={total_frames}")
            cap.release()
            return None, None

        logger.info(f"开始分析视频: {os.path.basename(video_path)} (FPS:{fps:.1f}, 帧数:{total_frames})")

        prev_frame = None
        motion_scores = []
        frame_count = 0

        # 处理进度显示间隔
        progress_interval = max(1, total_frames // 20)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 降采样加速处理
            small_frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None:
                # 计算帧差
                diff = cv2.absdiff(prev_frame, gray)

                # 统计显著变化的像素
                changed_pixels = np.sum(diff > pixel_threshold)
                total_pixels = gray.shape[0] * gray.shape[1]
                change_ratio = changed_pixels / total_pixels

                # 记录运动分数
                motion_scores.append(change_ratio)

            prev_frame = gray.copy()
            frame_count += 1

            # 显示进度
            if frame_count % progress_interval == 0:
                progress = (frame_count / total_frames) * 100
                logger.info(f"分析进度: {progress:.1f}% ({frame_count}/{total_frames})")

        cap.release()

        if not motion_scores:
            logger.error("未能提取运动分数")
            return None, None

        logger.info(f"运动检测完成，共分析 {len(motion_scores)} 帧")

        # 应用平滑
        smoothed_scores = self.smooth_motion_scores(motion_scores)

        # 检测无操作片段
        idle_segments = self.detect_idle_segments(smoothed_scores, fps, idle_threshold, self.min_segment_duration)

        return smoothed_scores, idle_segments

    def smooth_motion_scores(self, scores, window_size=3):
        """平滑运动分数"""
        if len(scores) < window_size:
            return scores

        smoothed = []
        for i in range(len(scores)):
            start = max(0, i - window_size // 2)
            end = min(len(scores), i + window_size // 2 + 1)
            avg_score = np.mean(scores[start:end])
            smoothed.append(avg_score)

        return smoothed

    def detect_idle_segments(self, motion_scores, fps, idle_threshold, min_duration):
        """检测无操作片段"""
        segments = []
        start_frame = None

        for i, score in enumerate(motion_scores):
            is_idle = score < idle_threshold

            if is_idle and start_frame is None:
                start_frame = i
            elif not is_idle and start_frame is not None:
                # 计算片段时长
                duration = (i - start_frame) / fps
                if duration >= min_duration:
                    segments.append({
                        'start_frame': start_frame,
                        'end_frame': i,
                        'start_time': start_frame / fps,
                        'end_time': i / fps,
                        'duration': duration
                    })
                start_frame = None

        # 处理视频结尾的无操作片段
        if start_frame is not None:
            duration = (len(motion_scores) - start_frame) / fps
            if duration >= min_duration:
                segments.append({
                    'start_frame': start_frame,
                    'end_frame': len(motion_scores),
                    'start_time': start_frame / fps,
                    'end_time': len(motion_scores) / fps,
                    'duration': duration
                })

        return segments

    def create_active_segments(self, idle_segments, total_duration, preserve_buffer=1.0):
        """根据无操作片段创建精彩片段列表"""
        active_segments = []

        if not idle_segments:
            # 如果没有无操作片段，整个视频都是精彩片段
            return [{'start_time': 0, 'end_time': total_duration}]

        current_time = 0

        for idle in idle_segments:
            # 在无操作片段之前的精彩片段
            segment_start = current_time
            segment_end = max(current_time, idle['start_time'] - preserve_buffer)

            if segment_end > segment_start + 0.5:  # 至少0.5秒的片段
                active_segments.append({
                    'start_time': segment_start,
                    'end_time': segment_end
                })

            # 跳过无操作片段，保留一点缓冲
            current_time = min(total_duration, idle['end_time'] + preserve_buffer)

        # 最后一个精彩片段
        if current_time < total_duration - 0.5:
            active_segments.append({
                'start_time': current_time,
                'end_time': total_duration
            })

        return active_segments

    def edit_video_segments(self, video_path, active_segments, output_path):
        """根据精彩片段剪辑视频"""
        if not active_segments:
            logger.warning(f"没有精彩片段，跳过: {os.path.basename(video_path)}")
            return False

        try:
            logger.info(f"开始剪辑: {os.path.basename(video_path)} -> {os.path.basename(output_path)}")
            logger.info(f"精彩片段数: {len(active_segments)}")

            # 检测音频
            has_audio = False
            try:
                probe = ffmpeg.probe(video_path)
                audio_streams = [s for s in probe['streams'] if s.get('codec_type') == 'audio']
                has_audio = len(audio_streams) > 0
                logger.info(f"音频检测: {'有音频' if has_audio else '无音频'}")
            except:
                logger.warning("音频检测失败，按无音频处理")

            # 如果只有一个片段，直接剪辑
            if len(active_segments) == 1:
                segment = active_segments[0]
                duration = segment['end_time'] - segment['start_time']

                input_stream = ffmpeg.input(video_path, ss=segment['start_time'], t=duration)

                if has_audio:
                    video_stream = input_stream.video
                    audio_stream = input_stream.audio
                    output_stream = ffmpeg.output(
                        video_stream, audio_stream, output_path,
                        vcodec='libx264', acodec='aac',
                        preset='medium', crf=23
                    )
                else:
                    video_stream = input_stream.video
                    output_stream = ffmpeg.output(
                        video_stream, output_path,
                        vcodec='libx264', preset='medium', crf=23
                    )

                ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            else:
                # 多个片段需要合并
                input_streams = []

                # 为每个片段创建输入流
                for i, segment in enumerate(active_segments):
                    duration = segment['end_time'] - segment['start_time']
                    input_stream = ffmpeg.input(video_path, ss=segment['start_time'], t=duration)
                    input_streams.append(input_stream)

                # 合并所有片段
                if has_audio:
                    # 提取视频和音频流
                    video_streams = [stream.video for stream in input_streams]
                    audio_streams = [stream.audio for stream in input_streams]

                    # 连接流
                    joined_video = ffmpeg.filter(video_streams, 'concat', n=len(video_streams), v=1, a=0)
                    joined_audio = ffmpeg.filter(audio_streams, 'concat', n=len(audio_streams), v=0, a=1)

                    output_stream = ffmpeg.output(
                        joined_video, joined_audio, output_path,
                        vcodec='libx264', acodec='aac',
                        preset='medium', crf=23
                    )
                else:
                    # 只有视频流
                    video_streams = [stream.video for stream in input_streams]
                    joined_video = ffmpeg.filter(video_streams, 'concat', n=len(video_streams))

                    output_stream = ffmpeg.output(
                        joined_video, output_path,
                        vcodec='libx264', preset='medium', crf=23
                    )

                ffmpeg.run(output_stream, overwrite_output=True, quiet=True)

            logger.info(f"剪辑完成: {os.path.basename(output_path)}")
            return True

        except Exception as e:
            logger.error(f"剪辑失败: {os.path.basename(video_path)} | 错误: {e}")
            return False

    def process_single_video(self, video_path, output_dir, idle_threshold, pixel_threshold, preserve_buffer, enable_preview):
        """处理单个视频文件"""
        try:
            filename = Path(video_path).stem
            output_filename = f"{filename}_edited.mp4"
            output_path = os.path.join(output_dir, output_filename)

            logger.info(f"处理视频: {os.path.basename(video_path)}")

            # 运动检测
            motion_scores, idle_segments = self.detect_motion_simple(
                video_path, idle_threshold, pixel_threshold
            )

            if motion_scores is None:
                logger.error(f"运动检测失败: {os.path.basename(video_path)}")
                return False, None

            # 获取视频总时长
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            total_duration = total_frames / fps if fps > 0 else 0
            cap.release()

            # 分析结果
            total_idle_time = sum([seg['duration'] for seg in idle_segments])
            active_time = total_duration - total_idle_time
            compression_ratio = (active_time / total_duration * 100) if total_duration > 0 else 0

            analysis_result = {
                'filename': os.path.basename(video_path),
                'total_duration': total_duration,
                'idle_segments_count': len(idle_segments),
                'total_idle_time': total_idle_time,
                'active_time': active_time,
                'compression_ratio': compression_ratio,
                'idle_segments': idle_segments
            }

            logger.info(f"分析结果: 总时长={total_duration:.1f}s, 无操作={total_idle_time:.1f}s, 压缩率={compression_ratio:.1f}%")

            # 如果是预览模式，不进行实际剪辑
            if enable_preview:
                logger.info(f"预览模式，跳过剪辑: {os.path.basename(video_path)}")
                return True, analysis_result

            # 创建精彩片段
            active_segments = self.create_active_segments(idle_segments, total_duration, preserve_buffer)

            if not active_segments:
                logger.warning(f"没有精彩片段: {os.path.basename(video_path)}")
                return False, analysis_result

            # 剪辑视频
            success = self.edit_video_segments(video_path, active_segments, output_path)

            if success:
                self.total_idle_time_removed += total_idle_time
                return True, analysis_result
            else:
                return False, analysis_result

        except Exception as e:
            logger.error(f"处理视频失败: {os.path.basename(video_path)} | 错误: {e}")
            return False, None

    def auto_edit_videos(self, input_folder: str, output_folder_prefix: str,
                        idle_threshold: float, min_segment_duration: float,
                        pixel_threshold: int, preserve_buffer: float = 1.0,
                        enable_preview: bool = False):
        """自动剪辑视频的主函数"""

        self.min_segment_duration = min_segment_duration  # 存储为实例变量

        try:
            logger.info(f"[GameVideoAutoEdit] 开始自动剪辑 | input_folder={input_folder} | output_prefix={output_folder_prefix}")
            logger.info(f"参数: idle_threshold={idle_threshold}, min_duration={min_segment_duration}s, pixel_threshold={pixel_threshold}")

            # 解析输入路径
            input_folder_path = resolve_path(input_folder)
            logger.info(f"解析后的输入路径: {input_folder_path}")

            if not os.path.exists(input_folder_path):
                logger.warning(f"输入路径不存在: {input_folder_path}")
                return ("", "输入路径不存在")

            # 创建输出目录
            output_dir = folder_paths.get_output_directory()
            unique_folder_name = generate_unique_folder_name(output_folder_prefix, output_dir)
            output_path = os.path.join(output_dir, unique_folder_name)
            os.makedirs(output_path, exist_ok=True)
            logger.info(f"输出目录: {output_path}")

            # 创建临时文件夹（处理文件名问题）
            temp_dir, filename_mapping = create_sanitized_temp_folder(input_folder_path)
            logger.info(f"临时目录: {temp_dir}")

            try:
                # 收集视频文件
                video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
                video_files = []
                for ext in video_extensions:
                    video_files.extend(glob.glob(os.path.join(temp_dir, ext)))

                if not video_files:
                    logger.warning("未找到视频文件")
                    return ("", "未找到视频文件")

                logger.info(f"找到 {len(video_files)} 个视频文件")

                # 重置统计信息
                self.processed_count = 0
                self.total_idle_time_removed = 0.0
                self.analysis_results = []

                # 并发处理视频
                max_workers = max(1, min(4, os.cpu_count() // 2))  # 限制并发数避免内存压力
                logger.info(f"使用 {max_workers} 个线程处理")

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_file = {
                        executor.submit(
                            self.process_single_video,
                            video_file, output_path, idle_threshold,
                            pixel_threshold, preserve_buffer, enable_preview
                        ): video_file
                        for video_file in video_files
                    }

                    for future in as_completed(future_to_file):
                        video_file = future_to_file[future]
                        try:
                            success, analysis_result = future.result()
                            if success:
                                self.processed_count += 1
                            if analysis_result:
                                self.analysis_results.append(analysis_result)
                        except Exception as e:
                            logger.error(f"处理异常: {os.path.basename(video_file)} | 错误: {e}")

                # 生成分析报告
                analysis_summary = self.generate_analysis_summary(enable_preview)

                if self.processed_count == 0:
                    return ("", "未成功处理任何视频")

                logger.info(f"处理完成: {self.processed_count}/{len(video_files)} 个视频")
                return (output_path, analysis_summary)

            finally:
                # 清理临时目录
                cleanup_temp_folder(temp_dir)

        except Exception as e:
            logger.error(f"自动剪辑失败: {e}")
            return ("", f"处理失败: {str(e)}")

    def generate_analysis_summary(self, enable_preview=False):
        """生成分析报告"""
        if not self.analysis_results:
            return "无分析结果"

        mode_text = "预览模式" if enable_preview else "剪辑模式"

        # 统计信息
        total_videos = len(self.analysis_results)
        total_original_duration = sum([r['total_duration'] for r in self.analysis_results])
        total_idle_time = sum([r['total_idle_time'] for r in self.analysis_results])
        total_active_time = sum([r['active_time'] for r in self.analysis_results])
        avg_compression = total_active_time / total_original_duration * 100 if total_original_duration > 0 else 0

        summary = f"""🎮 游戏视频自动剪辑分析报告 ({mode_text})

📊 总体统计:
- 处理视频数量: {total_videos}
- 成功处理: {self.processed_count}
- 原始总时长: {total_original_duration:.1f}秒 ({total_original_duration/60:.1f}分钟)
- 无操作总时长: {total_idle_time:.1f}秒 ({total_idle_time/60:.1f}分钟)
- 精彩内容时长: {total_active_time:.1f}秒 ({total_active_time/60:.1f}分钟)
- 平均压缩率: {avg_compression:.1f}%

📋 详细分析:"""

        for i, result in enumerate(self.analysis_results[:10], 1):  # 只显示前10个
            summary += f"""
{i}. {result['filename']}
   - 原时长: {result['total_duration']:.1f}s
   - 无操作片段: {result['idle_segments_count']}个, {result['total_idle_time']:.1f}s
   - 压缩率: {result['compression_ratio']:.1f}%"""

        if len(self.analysis_results) > 10:
            summary += f"\n   ... 还有 {len(self.analysis_results) - 10} 个视频"

        if not enable_preview:
            summary += f"\n\n✅ 剪辑完成，节省了 {total_idle_time/60:.1f} 分钟的观看时间！"
        else:
            summary += f"\n\n🔍 预览模式完成，可调整参数后正式剪辑"

        return summary


# 节点映射
NODE_CLASS_MAPPINGS = {
    "GameVideoAutoEditNode": GameVideoAutoEditNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GameVideoAutoEditNode": "游戏视频自动剪辑"
}