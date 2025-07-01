import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.schemas.multitrack_project import (
    MultitrackProject, 
    ProjectInfo, 
    Track, 
    AudioClip, 
    Character, 
    Marker
)

class ConversionService:
    """
    格式转换服务 - 将现有JSON格式转换为标准多音轨格式
    """
    
    async def convert_to_standard_format(
        self,
        dialogue_data: Dict[str, Any],
        environment_data: Optional[Dict[str, Any]] = None,
        background_music: Optional[Dict[str, Any]] = None,
        project_info: Optional[Dict[str, Any]] = None
    ) -> MultitrackProject:
        """
        将角色对话JSON和环境音JSON转换为标准多音轨格式
        """
        
        # 创建项目信息
        project = self._create_project_info(dialogue_data, project_info)
        
        # 转换对话音轨
        dialogue_track = await self._convert_dialogue_track(dialogue_data)
        
        # 转换环境音轨
        environment_track = await self._convert_environment_track(environment_data)
        
        # 转换背景音乐轨
        background_track = await self._convert_background_track(background_music)
        
        # 生成时间标记
        markers = self._generate_markers(dialogue_data, environment_data)
        
        # 计算总时长
        total_duration = self._calculate_total_duration([dialogue_track, environment_track, background_track])
        project.totalDuration = total_duration
        
        return MultitrackProject(
            project=project,
            tracks=[dialogue_track, environment_track, background_track],
            markers=markers
        )
    
    def _create_project_info(self, dialogue_data: Dict[str, Any], project_info: Optional[Dict[str, Any]]) -> ProjectInfo:
        """
        创建项目信息
        """
        default_info = {
            "id": f"project_{uuid.uuid4()}",
            "title": "多角色朗读项目",
            "description": "AI生成的多角色小说朗读音频合成项目",
            "author": "AI-Sound",
            "createdAt": datetime.now(),
            "sampleRate": 44100,
            "channels": 2,
            "bitDepth": 16,
            "exportFormat": "wav"
        }
        
        if project_info:
            default_info.update(project_info)
            
        # 从对话数据中提取标题（如果存在）
        if "title" in dialogue_data:
            default_info["title"] = dialogue_data["title"]
        elif "story_title" in dialogue_data:
            default_info["title"] = dialogue_data["story_title"]
            
        return ProjectInfo(**default_info)
    
    async def _convert_dialogue_track(self, dialogue_data: Dict[str, Any]) -> Track:
        """
        转换对话音轨
        """
        clips = []
        characters = {}
        current_time = 0.0
        
        # 解析对话数据
        dialogues = dialogue_data.get("dialogues", [])
        if not dialogues and "segments" in dialogue_data:
            dialogues = dialogue_data["segments"]
        
        for i, dialogue in enumerate(dialogues):
            # 提取角色信息
            character_name = dialogue.get("character", dialogue.get("speaker", f"角色{i+1}"))
            voice_id = dialogue.get("voice", dialogue.get("voice_id", "default"))
            
            # 创建角色记录
            if character_name not in characters:
                characters[character_name] = Character(
                    id=f"char_{len(characters) + 1}",
                    name=character_name,
                    voice=voice_id,
                    color=self._get_character_color(len(characters)),
                    avatar=""
                )
            
            # 创建音频片段
            start_time = dialogue.get("start_time", current_time)
            duration = dialogue.get("duration", 3.0)  # 默认3秒
            file_path = dialogue.get("file_path", dialogue.get("audio_file", ""))
            
            clip = AudioClip(
                id=f"dialogue_{i+1}",
                name=dialogue.get("text", f"对话 {i+1}")[:30] + "...",
                filePath=file_path,
                startTime=start_time,
                duration=duration,
                volume=dialogue.get("volume", 1.0),
                fadeIn=dialogue.get("fade_in", 0.1),
                fadeOut=dialogue.get("fade_out", 0.1),
                metadata={
                    "text": dialogue.get("text", ""),
                    "character": character_name,
                    "voice": voice_id,
                    "emotion": dialogue.get("emotion", "neutral")
                }
            )
            
            clips.append(clip)
            current_time = start_time + duration + 0.5  # 添加间隙
        
        return Track(
            id="track_dialogue",
            name="角色对话",
            type="dialogue",
            clips=clips,
            volume=1.0,
            muted=False,
            solo=False,
            color="#3498db",
            order=1,
            metadata={
                "characters": [char.dict() for char in characters.values()],
                "total_dialogues": len(clips)
            }
        )
    
    async def _convert_environment_track(self, environment_data: Optional[Dict[str, Any]]) -> Track:
        """
        转换环境音轨
        """
        clips = []
        
        if environment_data:
            environments = environment_data.get("environments", [])
            if not environments and "effects" in environment_data:
                environments = environment_data["effects"]
            
            for i, env in enumerate(environments):
                clip = AudioClip(
                    id=f"env_{i+1}",
                    name=env.get("name", f"环境音 {i+1}"),
                    filePath=env.get("file_path", env.get("audio_file", "")),
                    startTime=env.get("start_time", 0.0),
                    duration=env.get("duration", 10.0),
                    volume=env.get("volume", 0.6),
                    fadeIn=env.get("fade_in", 1.0),
                    fadeOut=env.get("fade_out", 1.0),
                    metadata={
                        "type": env.get("type", "ambient"),
                        "description": env.get("description", ""),
                        "loop": env.get("loop", True)
                    }
                )
                clips.append(clip)
        
        return Track(
            id="track_environment",
            name="环境音效",
            type="environment",
            clips=clips,
            volume=0.8,
            muted=False,
            solo=False,
            color="#27ae60",
            order=2,
            metadata={
                "total_effects": len(clips)
            }
        )
    
    async def _convert_background_track(self, background_music: Optional[Dict[str, Any]]) -> Track:
        """
        转换背景音乐轨
        """
        clips = []
        
        if background_music:
            # 处理单个背景音乐文件
            if "file_path" in background_music or "audio_file" in background_music:
                clip = AudioClip(
                    id="bg_music_1",
                    name=background_music.get("name", "背景音乐"),
                    filePath=background_music.get("file_path", background_music.get("audio_file", "")),
                    startTime=background_music.get("start_time", 0.0),
                    duration=background_music.get("duration", 60.0),
                    volume=background_music.get("volume", 0.3),
                    fadeIn=background_music.get("fade_in", 2.0),
                    fadeOut=background_music.get("fade_out", 2.0),
                    metadata={
                        "genre": background_music.get("genre", ""),
                        "mood": background_music.get("mood", ""),
                        "loop": background_music.get("loop", True)
                    }
                )
                clips.append(clip)
            
            # 处理多个背景音乐
            elif "music_tracks" in background_music:
                for i, music in enumerate(background_music["music_tracks"]):
                    clip = AudioClip(
                        id=f"bg_music_{i+1}",
                        name=music.get("name", f"背景音乐 {i+1}"),
                        filePath=music.get("file_path", music.get("audio_file", "")),
                        startTime=music.get("start_time", 0.0),
                        duration=music.get("duration", 30.0),
                        volume=music.get("volume", 0.3),
                        fadeIn=music.get("fade_in", 2.0),
                        fadeOut=music.get("fade_out", 2.0),
                        metadata={
                            "genre": music.get("genre", ""),
                            "mood": music.get("mood", "")
                        }
                    )
                    clips.append(clip)
        
        return Track(
            id="track_background",
            name="背景音乐",
            type="background",
            clips=clips,
            volume=0.5,
            muted=False,
            solo=False,
            color="#e74c3c",
            order=3,
            metadata={
                "total_music": len(clips)
            }
        )
    
    def _generate_markers(self, dialogue_data: Dict[str, Any], environment_data: Optional[Dict[str, Any]]) -> List[Marker]:
        """
        生成时间标记
        """
        markers = []
        
        # 从对话数据生成章节标记
        dialogues = dialogue_data.get("dialogues", dialogue_data.get("segments", []))
        
        # 添加开始标记
        markers.append(Marker(
            id="marker_start",
            name="开始",
            time=0.0,
            type="chapter",
            color="#9b59b6"
        ))
        
        # 每10个对话添加一个章节标记
        for i in range(0, len(dialogues), 10):
            if i > 0:
                dialogue = dialogues[i]
                markers.append(Marker(
                    id=f"marker_chapter_{i//10 + 1}",
                    name=f"第 {i//10 + 1} 章节",
                    time=dialogue.get("start_time", i * 3.0),
                    type="chapter",
                    color="#9b59b6"
                ))
        
        return markers
    
    def _calculate_total_duration(self, tracks: List[Track]) -> float:
        """
        计算总时长
        """
        max_duration = 0.0
        
        for track in tracks:
            for clip in track.clips:
                end_time = clip.startTime + clip.duration
                max_duration = max(max_duration, end_time)
        
        return max_duration
    
    def _get_character_color(self, index: int) -> str:
        """
        获取角色颜色
        """
        colors = [
            "#3498db", "#e74c3c", "#2ecc71", "#f39c12", 
            "#9b59b6", "#1abc9c", "#34495e", "#e67e22"
        ]
        return colors[index % len(colors)] 