from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from enum import Enum
from app.database import Base

class AudioCategory(str, Enum):
    """音频文件分类枚举"""
    dialogue = "dialogue"      # 对话音
    environment = "environment"  # 环境音
    theme = "theme"           # 主题音

class AudioFile(Base):
    """音频文件模型"""
    __tablename__ = "audio_files"
    
    file_id = Column(String, primary_key=True, index=True)
    original_name = Column(String, nullable=False, comment="原始文件名")
    file_path = Column(String, nullable=False, comment="文件存储路径")
    category = Column(SQLEnum(AudioCategory), default=AudioCategory.dialogue, comment="文件分类")
    project_id = Column(String, nullable=True, comment="关联项目ID")
    
    # 文件元数据
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    duration = Column(Float, nullable=True, comment="音频时长(秒)")
    sample_rate = Column(Integer, nullable=True, comment="采样率")
    channels = Column(Integer, nullable=True, comment="声道数")
    format = Column(String, nullable=True, comment="音频格式")
    codec = Column(String, nullable=True, comment="编解码器")
    bitrate = Column(Integer, nullable=True, comment="比特率")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "filename": self.original_name,  # 兼容前端
            "file_path": self.file_path,
            "category": self.category.value if self.category else "dialogue",
            "project_id": self.project_id,
            "file_size": self.file_size,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "format": self.format,
            "codec": self.codec,
            "bitrate": self.bitrate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "upload_time": self.created_at.timestamp() if self.created_at else None,
        }