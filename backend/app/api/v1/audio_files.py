from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import tempfile
import uuid

from app.services.audio.upload_service import AudioUploadService
from app.services.audio.ffmpeg_service import FFmpegService

router = APIRouter()

# 服务实例
upload_service = AudioUploadService()
ffmpeg_service = FFmpegService()


@router.post("/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    category: str = "dialogue",
    project_id: Optional[str] = None
):
    """
    上传单个音频文件
    """
    # 验证分类参数
    valid_categories = ["dialogue", "environment", "theme"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"无效的分类: {category}. 有效分类: {valid_categories}")
    
    try:
        result = await upload_service.upload_audio_file(file, category, project_id)
        return {
            "success": True,
            "message": "文件上传成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/multiple")
async def upload_multiple_audio_files(
    files: List[UploadFile] = File(...),
    category: str = "dialogue",
    project_id: Optional[str] = None
):
    """
    批量上传音频文件
    """
    if len(files) > 10:  # 限制单次上传文件数量
        raise HTTPException(status_code=400, detail="单次最多上传10个文件")
    
    # 验证分类参数
    valid_categories = ["dialogue", "environment", "theme"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"无效的分类: {category}. 有效分类: {valid_categories}")
    
    try:
        results = await upload_service.upload_multiple_files(files, category, project_id)
        
        success_count = sum(1 for r in results if r.get('upload_success', False))
        
        return {
            "success": True,
            "message": f"上传完成，成功: {success_count}/{len(files)}",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_audio_files(project_id: Optional[str] = None):
    """
    获取已上传的音频文件列表
    """
    try:
        files = await upload_service.list_uploaded_files(project_id)
        return {
            "success": True,
            "data": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{file_id}")
async def get_audio_file_info(file_id: str):
    """
    获取音频文件详细信息
    """
    try:
        info = await upload_service.get_file_info(file_id)
        if not info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "success": True,
            "data": info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/waveform/{file_id}")
async def get_audio_waveform(file_id: str, width: int = 800, height: int = 100):
    """
    获取音频文件波形数据
    """
    try:
        info = await upload_service.get_file_info(file_id)
        if not info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        waveform_data = await ffmpeg_service.extract_waveform_data(
            info['file_path'], width, height
        )
        
        return {
            "success": True,
            "data": {
                "file_id": file_id,
                "width": width,
                "height": height,
                "waveform": waveform_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert/{file_id}")
async def convert_audio_file(
    file_id: str, 
    output_format: str = "wav",
    sample_rate: int = 44100
):
    """
    转换音频文件格式
    """
    try:
        output_path = await upload_service.convert_to_standard_format(
            file_id, output_format, sample_rate
        )
        
        if not output_path:
            raise HTTPException(status_code=404, detail="文件不存在或转换失败")
        
        return {
            "success": True,
            "message": "转换完成",
            "data": {
                "file_id": file_id,
                "output_path": output_path,
                "format": output_format,
                "sample_rate": sample_rate
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_id}")
async def delete_audio_file(file_id: str):
    """
    删除音频文件
    """
    try:
        success = await upload_service.delete_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "success": True,
            "message": "文件删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_audio_file(file_id: str):
    """
    下载音频文件
    """
    try:
        info = await upload_service.get_file_info(file_id)
        if not info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path = info['file_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        filename = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trim/{file_id}")
async def trim_audio_file(
    file_id: str,
    start_time: float,
    duration: float
):
    """
    裁剪音频文件
    """
    try:
        info = await upload_service.get_file_info(file_id)
        if not info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 生成输出文件路径
        import uuid
        trim_id = str(uuid.uuid4())
        output_filename = f"{trim_id}_trimmed.wav"
        output_path = os.path.join(upload_service.upload_dir, output_filename)
        
        result_path = await ffmpeg_service.trim_audio(
            info['file_path'], output_path, start_time, duration
        )
        
        # 获取裁剪后文件信息
        trimmed_info = await ffmpeg_service.get_audio_info(result_path)
        
        return {
            "success": True,
            "message": "音频裁剪成功",
            "data": {
                "trim_id": trim_id,
                "output_path": result_path,
                "start_time": start_time,
                "duration": duration,
                "file_info": trimmed_info
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-upload")
async def verify_upload_file(file: UploadFile = File(...)):
    """
    验证上传文件的原始信息（不保存文件）
    """
    try:
        # 临时保存文件用于检查
        import tempfile
        import uuid
        
        temp_id = str(uuid.uuid4())
        temp_path = f"/tmp/verify_{temp_id}_{file.filename}"
        
        # 保存临时文件
        content = await file.read()
        with open(temp_path, "wb") as temp_file:
            temp_file.write(content)
        
        # 获取文件信息
        file_info = await ffmpeg_service.get_audio_info(temp_path)
        
        # 清理临时文件
        os.unlink(temp_path)
        
        return {
            "success": True,
            "message": "文件验证完成",
            "data": {
                "original_filename": file.filename,
                "file_size_bytes": len(content),
                "file_size_mb": round(len(content) / 1024 / 1024, 2),
                "duration_seconds": file_info['duration'],
                "duration_formatted": f"{int(file_info['duration'] // 60)}:{int(file_info['duration'] % 60):02d}",
                "sample_rate": file_info['sample_rate'],
                "channels": file_info['channels'],
                "bitrate": file_info['bitrate'],
                "format": file_info['format'],
                "codec": file_info['codec']
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"文件验证失败: {str(e)}"
        }


@router.get("/health")
async def audio_service_health():
    """
    检查音频服务健康状态
    """
    try:
        ffmpeg_available = ffmpeg_service.is_available()
        
        return {
            "success": True,
            "data": {
                "ffmpeg_available": ffmpeg_available,
                "upload_dir": upload_service.upload_dir,
                "max_file_size": upload_service.max_file_size,
                "allowed_extensions": list(upload_service.allowed_extensions)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }