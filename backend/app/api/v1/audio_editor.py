import uuid
import os
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from app.schemas.audio_mix import AudioMixRequest, AudioMixResponse
from app.services.audio_mix_service import AudioMixService

router = APIRouter()

@router.post("/mix", response_model=AudioMixResponse)
async def mix_audio(request: AudioMixRequest, background_tasks: BackgroundTasks):
    """
    多轨音频合成任务（异步）
    """
    # 生成唯一任务ID
    task_id = str(uuid.uuid4())
    
    # 初始化服务
    service = AudioMixService()
    
    # 添加后台任务
    background_tasks.add_task(service.mix_tracks, request, task_id)
    
    return AudioMixResponse(
        task_id=task_id, 
        status="processing", 
        message="任务已提交，正在处理中..."
    )

@router.get("/task/{task_id}", response_model=AudioMixResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态
    """
    # 检查输出文件是否存在
    output_path = f"outputs/{task_id}.wav"
    
    if os.path.exists(output_path):
        return AudioMixResponse(
            task_id=task_id,
            status="completed",
            message="音频合成完成",
            output_url=f"/api/v1/audio-editor/download/{task_id}.wav"
        )
    else:
        return AudioMixResponse(
            task_id=task_id,
            status="processing",
            message="任务处理中..."
        )

@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载合成的音频文件
    """
    file_path = f"outputs/{filename}"
    
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/wav'
        )
    else:
        return {"error": "文件不存在"}
