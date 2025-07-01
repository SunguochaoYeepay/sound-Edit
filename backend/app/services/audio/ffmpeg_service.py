import os
import subprocess
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class FFmpegService:
    """
    FFmpeg音频处理服务
    提供音频文件分析、转换、合成等功能
    """
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg可执行文件路径"""
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # 常见安装路径
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            'ffmpeg'  # 系统PATH中
        ]
        
        for path in common_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return path
            except:
                continue
                
        raise RuntimeError("FFmpeg未找到，请确保已安装FFmpeg")
    
    def _find_ffprobe(self) -> str:
        """查找FFprobe可执行文件路径"""
        try:
            result = subprocess.run(['which', 'ffprobe'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
            
        # 通常与ffmpeg在同一目录
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
        ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe')
        
        try:
            subprocess.run([ffprobe_path, '-version'], capture_output=True, check=True)
            return ffprobe_path
        except:
            pass
            
        raise RuntimeError("FFprobe未找到")
    
    async def get_audio_info(self, file_path: str) -> Dict:
        """
        获取音频文件信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "无错误信息"
                print(f"FFprobe错误 - 返回码: {process.returncode}, 错误信息: {error_msg}")
                print(f"FFprobe命令: {' '.join(cmd)}")
                raise RuntimeError(f"FFprobe执行失败: {error_msg}")
            
            info = json.loads(stdout.decode())
            
            # 提取音频流信息
            audio_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("文件中未找到音频流")
            
            # 格式化返回信息
            return {
                'duration': float(info['format'].get('duration', 0)),
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'size': int(info['format'].get('size', 0)),
                'format': info['format'].get('format_name', ''),
                'sample_rate': int(audio_stream.get('sample_rate', 44100)),
                'channels': int(audio_stream.get('channels', 2)),
                'codec': audio_stream.get('codec_name', ''),
                'file_path': file_path
            }
            
        except json.JSONDecodeError:
            raise RuntimeError("解析FFprobe输出失败")
        except Exception as e:
            raise RuntimeError(f"获取音频信息失败: {str(e)}")
    
    async def convert_audio(self, input_path: str, output_path: str, 
                          format: str = 'wav', sample_rate: int = 44100,
                          channels: int = 2, bitrate: Optional[str] = None) -> str:
        """
        转换音频格式
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-y'  # 覆盖输出文件
        ]
        
        if bitrate:
            cmd.extend(['-b:a', bitrate])
        
        cmd.append(output_path)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"音频转换失败: {stderr.decode()}")
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"音频转换失败: {str(e)}")
    
    async def extract_waveform_data(self, file_path: str, width: int = 800, 
                                  height: int = 100) -> List[float]:
        """
        提取音频波形数据，用于前端显示
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        # 使用ffmpeg生成音频样本数据
        cmd = [
            self.ffmpeg_path,
            '-i', file_path,
            '-ac', '1',  # 转为单声道
            '-ar', '8000',  # 降低采样率以减少数据量
            '-f', 'f32le',  # 输出32位浮点格式
            '-'
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"提取波形失败: {stderr.decode()}")
            
            # 将二进制数据转换为浮点数组
            import struct
            samples = []
            for i in range(0, len(stdout), 4):
                if i + 4 <= len(stdout):
                    sample = struct.unpack('<f', stdout[i:i+4])[0]
                    samples.append(sample)
            
            # 重采样到指定宽度
            if len(samples) > width:
                # 简单的平均重采样
                chunk_size = len(samples) // width
                resampled = []
                for i in range(width):
                    start = i * chunk_size
                    end = min(start + chunk_size, len(samples))
                    if start < len(samples):
                        chunk = samples[start:end]
                        avg = sum(abs(s) for s in chunk) / len(chunk) if chunk else 0
                        resampled.append(avg)
                return resampled
            
            return [abs(s) for s in samples]
            
        except Exception as e:
            raise RuntimeError(f"提取波形失败: {str(e)}")
    
    async def mix_audio_tracks(self, tracks: List[Dict], output_path: str, 
                             total_duration: float, sample_rate: int = 44100) -> str:
        """
        混合多个音轨
        tracks: [
            {
                'file_path': str,
                'start_time': float,
                'duration': float,
                'volume': float,
                'fade_in': float,
                'fade_out': float
            }
        ]
        """
        if not tracks:
            raise ValueError("没有音轨数据")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 构建复杂的FFmpeg命令
        cmd = [self.ffmpeg_path]
        
        # 添加所有输入文件
        input_files = []
        for i, track in enumerate(tracks):
            if os.path.exists(track['file_path']):
                cmd.extend(['-i', track['file_path']])
                input_files.append(i)
        
        if not input_files:
            raise ValueError("没有有效的音频文件")
        
        # 构建滤镜图
        filter_complex = []
        
        for i, track in enumerate(tracks):
            if not os.path.exists(track['file_path']):
                continue
                
            input_idx = input_files.index(i) if i in input_files else None
            if input_idx is None:
                continue
            
            # 音量调节
            volume_filter = f"[{input_idx}:a]volume={track['volume']}"
            
            # 淡入淡出
            if track.get('fade_in', 0) > 0:
                volume_filter += f",afade=t=in:st=0:d={track['fade_in']}"
            if track.get('fade_out', 0) > 0:
                duration = track.get('duration', 0)
                fade_start = max(0, duration - track['fade_out'])
                volume_filter += f",afade=t=out:st={fade_start}:d={track['fade_out']}"
            
            # 时间偏移
            if track.get('start_time', 0) > 0:
                volume_filter += f",adelay={int(track['start_time'] * 1000)}|{int(track['start_time'] * 1000)}"
            
            volume_filter += f"[a{i}]"
            filter_complex.append(volume_filter)
        
        # 混合所有音轨
        mix_inputs = ''.join([f"[a{i}]" for i, track in enumerate(tracks) 
                             if os.path.exists(track['file_path'])])
        mix_filter = f"{mix_inputs}amix=inputs={len([t for t in tracks if os.path.exists(t['file_path'])])}:duration=longest[out]"
        filter_complex.append(mix_filter)
        
        # 添加滤镜复合参数
        cmd.extend([
            '-filter_complex', ';'.join(filter_complex),
            '-map', '[out]',
            '-ar', str(sample_rate),
            '-ac', '2',  # 立体声输出
            '-t', str(total_duration),  # 限制输出时长
            '-y',  # 覆盖输出文件
            output_path
        ])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"音频混合失败: {stderr.decode()}")
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"音频混合失败: {str(e)}")
    
    async def trim_audio(self, input_path: str, output_path: str, 
                        start_time: float, duration: float) -> str:
        """
        裁剪音频片段
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # 复制编码，不重新编码
            '-y',
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"音频裁剪失败: {stderr.decode()}")
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"音频裁剪失败: {str(e)}")
    
    def is_available(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            subprocess.run([self.ffmpeg_path, '-version'], 
                          capture_output=True, check=True)
            return True
        except:
            return False