from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TrackType(str, Enum):
    dialogue = "dialogue"
    environment = "environment" 
    background = "background"

class ProjectInfo(BaseModel):
    id: str = Field(..., description="项目唯一标识")
    title: str = Field(..., description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    author: Optional[str] = Field(None, description="项目作者")
    totalDuration: float = Field(0.0, description="总时长（秒）")
    sampleRate: int = Field(44100, description="采样率")
    channels: int = Field(2, description="声道数")
    bitDepth: int = Field(16, description="位深度")
    exportFormat: str = Field("wav", description="导出格式")
    createdAt: Optional[datetime] = Field(None, description="创建时间")
    version: str = Field("1.0", description="格式版本")

class Character(BaseModel):
    id: str = Field(..., description="角色唯一标识")
    name: str = Field(..., description="角色名称")
    voice: str = Field(..., description="语音模型标识")
    color: str = Field(..., description="角色颜色")
    avatar: Optional[str] = Field(None, description="角色头像路径")

class AudioClip(BaseModel):
    id: str = Field(..., description="片段唯一标识")
    name: str = Field(..., description="片段名称")
    filePath: str = Field(..., description="音频文件路径")
    startTime: float = Field(..., description="开始时间（秒）")
    duration: float = Field(..., description="持续时间（秒）")
    volume: float = Field(1.0, description="片段音量")
    fadeIn: float = Field(0.0, description="淡入时长（秒）")
    fadeOut: float = Field(0.0, description="淡出时长（秒）")
    playbackRate: float = Field(1.0, description="播放速度")
    loop: Optional[bool] = Field(False, description="是否循环播放")
    character: Optional[Character] = Field(None, description="角色信息（对话轨专用）")
    text: Optional[str] = Field(None, description="原始文本内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")

class Track(BaseModel):
    id: str = Field(..., description="轨道唯一标识")
    name: str = Field(..., description="轨道名称")
    type: TrackType = Field(..., description="轨道类型")
    volume: float = Field(1.0, description="轨道整体音量")
    muted: bool = Field(False, description="是否静音")
    solo: bool = Field(False, description="是否独奏")
    color: str = Field(..., description="轨道颜色")
    order: int = Field(..., description="轨道排序")
    clips: List[AudioClip] = Field(default_factory=list, description="音频片段列表")

class Marker(BaseModel):
    id: str = Field(..., description="标记唯一标识")
    name: str = Field(..., description="标记名称")
    time: float = Field(..., description="时间点（秒）")
    type: str = Field("marker", description="标记类型")
    color: str = Field(..., description="标记颜色")

class MultitrackProject(BaseModel):
    project: ProjectInfo = Field(..., description="项目信息")
    tracks: List[Track] = Field(default_factory=list, description="音轨列表")
    markers: Optional[List[Marker]] = Field(default_factory=list, description="时间标记")

# API响应模型
class MultitrackProjectResponse(BaseModel):
    success: bool = Field(True, description="操作是否成功")
    data: Optional[MultitrackProject] = Field(None, description="项目数据")
    message: Optional[str] = Field(None, description="响应消息")

class MultitrackProjectRequest(BaseModel):
    project: MultitrackProject = Field(..., description="多音轨项目数据")

# 转换工具的数据模型
class DialogueData(BaseModel):
    """原始角色对话数据格式"""
    characters: List[Dict[str, Any]]
    dialogues: List[Dict[str, Any]]

class EnvironmentData(BaseModel):
    """原始环境音数据格式"""
    scenes: List[Dict[str, Any]]
    effects: List[Dict[str, Any]]

class ConversionRequest(BaseModel):
    """格式转换请求"""
    dialogueData: Dict[str, Any] = Field(..., description="角色对话数据")
    environmentData: Optional[Dict[str, Any]] = Field(None, description="环境音数据")
    backgroundMusic: Optional[Dict[str, Any]] = Field(None, description="背景音乐配置")
    projectInfo: Optional[Dict[str, Any]] = Field(None, description="项目基本信息") 