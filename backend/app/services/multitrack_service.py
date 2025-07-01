import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.schemas.multitrack_project import MultitrackProject, ProjectInfo
from app.services.audio_mix_service import AudioMixService
from app.services.audio.ffmpeg_service import FFmpegService

class MultitrackService:
    """
    多音轨项目管理服务
    """
    
    def __init__(self):
        self.projects_dir = "projects"
        self.exports_dir = "exports"
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        self.ffmpeg_service = FFmpegService()
        
    async def create_project(self, project: MultitrackProject) -> MultitrackProject:
        """
        创建新的多音轨项目
        """
        # 确保项目ID唯一
        if not project.project.id:
            project.project.id = f"project_{uuid.uuid4()}"
            
        # 设置创建时间
        if not project.project.createdAt:
            project.project.createdAt = datetime.now()
            
        # 保存项目文件
        await self._save_project_file(project.project.id, project)
        
        return project
    
    async def load_project(self, project_id: str) -> Optional[MultitrackProject]:
        """
        加载多音轨项目
        """
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        
        if not os.path.exists(project_file):
            return None
            
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                return MultitrackProject(**project_data)
        except Exception as e:
            print(f"加载项目 {project_id} 失败: {e}")
            return None
    
    async def save_project(self, project_id: str, project: MultitrackProject) -> MultitrackProject:
        """
        保存多音轨项目
        """
        # 确保项目ID一致
        project.project.id = project_id
        
        # 保存项目文件
        await self._save_project_file(project_id, project)
        
        return project
    
    async def list_projects(self) -> List[ProjectInfo]:
        """
        获取所有项目列表
        """
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
            
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_id = filename[:-5]  # 移除 .json 后缀
                project = await self.load_project(project_id)
                if project:
                    projects.append(project.project)
                    
        return sorted(projects, key=lambda x: x.createdAt or datetime.min, reverse=True)
    
    async def delete_project(self, project_id: str) -> bool:
        """
        删除多音轨项目
        """
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        
        if not os.path.exists(project_file):
            return False
            
        try:
            os.remove(project_file)
            return True
        except Exception as e:
            print(f"删除项目 {project_id} 失败: {e}")
            return False
    
    async def export_project_audio(self, project_id: str, export_task_id: str):
        """
        导出多音轨项目为音频文件（后台任务）
        """
        try:
            # 加载项目
            project = await self.load_project(project_id)
            if not project:
                await self._save_export_status(export_task_id, "failed", "项目不存在")
                return
                
            # 更新导出状态
            await self._save_export_status(export_task_id, "processing", "正在处理音频...")
            
            # 转换为音频合成请求格式
            audio_tracks = []
            for track in project.tracks:
                if track.muted:
                    continue
                    
                for clip in track.clips:
                    # 检查文件是否存在
                    if not os.path.exists(clip.filePath):
                        print(f"警告: 音频文件不存在 {clip.filePath}")
                        continue
                        
                    audio_tracks.append({
                        "file_path": clip.filePath,
                        "start_time": clip.startTime,
                        "duration": clip.duration,
                        "volume": clip.volume * track.volume,
                        "fade_in": clip.fadeIn,
                        "fade_out": clip.fadeOut
                    })
            
            if not audio_tracks:
                await self._save_export_status(export_task_id, "failed", "没有有效的音频文件")
                return
            
            # 使用FFmpeg进行实际音频合成
            output_format = project.project.exportFormat or "wav"
            output_path = os.path.join(self.exports_dir, f"{export_task_id}.{output_format}")
            
            # 调用FFmpeg服务进行音频混合
            try:
                result_path = await self.ffmpeg_service.mix_audio_tracks(
                    audio_tracks, 
                    output_path, 
                    project.project.totalDuration,
                    project.project.sampleRate or 44100
                )
                
                # 验证输出文件
                if not os.path.exists(result_path):
                    raise RuntimeError("音频合成完成但输出文件不存在")
                    
            except Exception as e:
                await self._save_export_status(export_task_id, "failed", f"音频合成失败: {str(e)}")
                return
            
            # 更新导出状态为完成
            await self._save_export_status(
                export_task_id, 
                "completed", 
                "导出完成",
                output_path
            )
            
        except Exception as e:
            await self._save_export_status(export_task_id, "failed", f"导出失败: {str(e)}")
    
    async def get_export_status(self, export_task_id: str) -> Dict[str, Any]:
        """
        获取导出任务状态
        """
        status_file = os.path.join(self.exports_dir, f"{export_task_id}_status.json")
        
        if not os.path.exists(status_file):
            return {
                "export_task_id": export_task_id,
                "status": "not_found",
                "message": "导出任务不存在"
            }
            
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {
                "export_task_id": export_task_id,
                "status": "error",
                "message": f"读取状态失败: {str(e)}"
            }
    
    async def get_exported_file_path(self, export_task_id: str) -> Optional[str]:
        """
        获取导出文件路径
        """
        status = await self.get_export_status(export_task_id)
        
        if status.get("status") == "completed" and status.get("output_path"):
            return status["output_path"]
            
        return None
    
    async def validate_project(self, project_id: str) -> Dict[str, Any]:
        """
        验证项目数据完整性
        """
        project = await self.load_project(project_id)
        
        if not project:
            return {
                "valid": False,
                "errors": ["项目不存在"]
            }
            
        errors = []
        warnings = []
        
        # 验证项目基本信息
        if not project.project.title:
            errors.append("项目标题不能为空")
            
        if project.project.totalDuration <= 0:
            errors.append("项目总时长必须大于0")
        
        # 验证音轨
        if not project.tracks:
            warnings.append("项目没有音轨")
        else:
            for track in project.tracks:
                # 验证音频文件是否存在
                for clip in track.clips:
                    if not os.path.exists(clip.filePath):
                        warnings.append(f"音频文件不存在: {clip.filePath}")
                        
                    # 验证时间范围
                    if clip.startTime < 0:
                        errors.append(f"音频片段 {clip.id} 开始时间不能为负数")
                        
                    if clip.duration <= 0:
                        errors.append(f"音频片段 {clip.id} 持续时间必须大于0")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "project_id": project_id
        }
    
    async def _save_project_file(self, project_id: str, project: MultitrackProject):
        """
        保存项目文件到磁盘
        """
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        
        # 转换为字典格式，处理datetime序列化
        project_dict = project.dict()
        if project_dict["project"]["createdAt"]:
            project_dict["project"]["createdAt"] = project_dict["project"]["createdAt"].isoformat()
            
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project_dict, f, ensure_ascii=False, indent=2)
    
    async def generate_preview_audio(self, project_id: str, start_time: float = 0, duration: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        生成项目音频预览
        """
        try:
            # 加载项目
            project = await self.load_project(project_id)
            if not project:
                return None
            
            # 生成预览文件ID
            preview_id = str(uuid.uuid4())
            
            # 计算预览时长（默认10秒或剩余时长）
            if duration is None:
                max_duration = project.project.totalDuration - start_time
                duration = min(10.0, max_duration)
            
            # 转换为音频合成请求格式
            audio_tracks = []
            for track in project.tracks:
                if track.muted:
                    continue
                    
                for clip in track.clips:
                    # 检查片段是否在预览时间范围内
                    clip_end = clip.startTime + clip.duration
                    preview_end = start_time + duration
                    
                    if clip_end <= start_time or clip.startTime >= preview_end:
                        continue  # 片段不在预览范围内
                    
                    # 检查文件是否存在
                    if not os.path.exists(clip.filePath):
                        print(f"警告: 音频文件不存在 {clip.filePath}")
                        continue
                    
                    # 计算相对于预览开始时间的偏移
                    relative_start = max(0, clip.startTime - start_time)
                    
                    audio_tracks.append({
                        "file_path": clip.filePath,
                        "start_time": relative_start,
                        "duration": clip.duration,
                        "volume": clip.volume * track.volume,
                        "fade_in": clip.fadeIn,
                        "fade_out": clip.fadeOut
                    })
            
            # 确保输出目录存在
            os.makedirs("outputs", exist_ok=True)
            
            # 生成预览音频文件
            output_path = f"outputs/preview_{preview_id}.wav"
            
            if audio_tracks:
                # 使用FFmpeg进行音频混合
                result_path = await self.ffmpeg_service.mix_audio_tracks(
                    audio_tracks,
                    output_path,
                    duration,
                    project.project.sampleRate or 44100
                )
            else:
                # 如果没有音频轨道，生成静音文件
                result_path = await self._generate_silence(output_path, duration)
            
            return {
                "preview_file": preview_id,
                "duration": duration,
                "sample_rate": project.project.sampleRate or 44100,
                "file_path": result_path
            }
            
        except Exception as e:
            print(f"生成预览音频失败: {e}")
            return None
    
    async def _generate_silence(self, output_path: str, duration: float) -> str:
        """
        生成指定时长的静音文件
        """
        cmd = [
            self.ffmpeg_service.ffmpeg_path,
            '-f', 'lavfi',
            '-i', f'anullsrc=r=44100:cl=stereo',
            '-t', str(duration),
            '-y', output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"生成静音文件失败: {stderr.decode()}")
        
        return output_path

    async def _save_export_status(self, export_task_id: str, status: str, message: str, output_path: str = None):
        """
        保存导出任务状态
        """
        status_file = os.path.join(self.exports_dir, f"{export_task_id}_status.json")
        
        status_data = {
            "export_task_id": export_task_id,
            "status": status,
            "message": message,
            "updated_at": datetime.now().isoformat()
        }
        
        if output_path:
            status_data["output_path"] = output_path
            
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2) 