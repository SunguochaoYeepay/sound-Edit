from pydantic import BaseModel, Field
from typing import List, Optional

class TrackConfig(BaseModel):
    file_path: str = Field(..., description="音频文件路径")
    start_time: float = Field(0, description="起始时间（秒）")
    end_time: Optional[float] = Field(None, description="结束时间（秒）")
    volume: float = Field(1.0, description="音量系数")
    fade_in: float = Field(0, description="淡入时长（秒）")
    fade_out: float = Field(0, description="淡出时长（秒）")

class AudioMixRequest(BaseModel):
    tracks: List[TrackConfig] = Field(..., description="多轨音频配置")
    output_format: str = Field("wav", description="输出格式")

class AudioMixResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    output_url: Optional[str] = None
