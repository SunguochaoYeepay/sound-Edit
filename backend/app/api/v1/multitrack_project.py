import uuid
import json
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.schemas.multitrack_project import (
    MultitrackProject, 
    MultitrackProjectResponse, 
    MultitrackProjectRequest,
    ConversionRequest,
    ProjectInfo
)
from app.services.multitrack_service import MultitrackService
from app.services.conversion_service import ConversionService

router = APIRouter()

@router.post("/create", response_model=MultitrackProjectResponse)
async def create_project(request: MultitrackProjectRequest):
    """
    创建新的多音轨项目
    """
    try:
        service = MultitrackService()
        project_data = await service.create_project(request.project)
        
        return MultitrackProjectResponse(
            success=True,
            data=project_data,
            message="项目创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")

@router.get("/load/{project_id}", response_model=MultitrackProjectResponse)
async def load_project(project_id: str):
    """
    加载多音轨项目
    """
    try:
        service = MultitrackService()
        project_data = await service.load_project(project_id)
        
        if not project_data:
            raise HTTPException(status_code=404, detail="项目不存在")
            
        return MultitrackProjectResponse(
            success=True,
            data=project_data,
            message="项目加载成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载项目失败: {str(e)}")

@router.put("/save/{project_id}", response_model=MultitrackProjectResponse)
async def save_project(project_id: str, request: MultitrackProjectRequest):
    """
    保存多音轨项目
    """
    try:
        service = MultitrackService()
        project_data = await service.save_project(project_id, request.project)
        
        return MultitrackProjectResponse(
            success=True,
            data=project_data,
            message="项目保存成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存项目失败: {str(e)}")

@router.get("/list", response_model=List[ProjectInfo])
async def list_projects():
    """
    获取所有项目列表
    """
    try:
        service = MultitrackService()
        projects = await service.list_projects()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.delete("/delete/{project_id}")
async def delete_project(project_id: str):
    """
    删除多音轨项目
    """
    try:
        service = MultitrackService()
        success = await service.delete_project(project_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")
            
        return {"success": True, "message": "项目删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")

@router.post("/convert", response_model=MultitrackProjectResponse)
async def convert_to_standard_format(request: ConversionRequest):
    """
    将角色对话JSON和环境音JSON转换为标准多音轨格式
    """
    try:
        conversion_service = ConversionService()
        project_data = await conversion_service.convert_to_standard_format(
            dialogue_data=request.dialogueData,
            environment_data=request.environmentData,
            background_music=request.backgroundMusic,
            project_info=request.projectInfo
        )
        
        return MultitrackProjectResponse(
            success=True,
            data=project_data,
            message="格式转换成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"格式转换失败: {str(e)}")

@router.post("/export/{project_id}")
async def export_project(project_id: str, background_tasks: BackgroundTasks):
    """
    导出多音轨项目为音频文件
    """
    try:
        service = MultitrackService()
        
        # 生成导出任务ID
        export_task_id = str(uuid.uuid4())
        
        # 添加后台导出任务
        background_tasks.add_task(
            service.export_project_audio, 
            project_id, 
            export_task_id
        )
        
        return {
            "success": True,
            "export_task_id": export_task_id,
            "message": "导出任务已开始，请查询任务状态"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动导出任务失败: {str(e)}")

@router.get("/export/status/{export_task_id}")
async def get_export_status(export_task_id: str):
    """
    查询导出任务状态
    """
    try:
        service = MultitrackService()
        status = await service.get_export_status(export_task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询导出状态失败: {str(e)}")

@router.get("/export/download/{export_task_id}")
async def download_exported_audio(export_task_id: str):
    """
    下载导出的音频文件
    """
    try:
        service = MultitrackService()
        file_path = await service.get_exported_file_path(export_task_id)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="导出文件不存在")
            
        return FileResponse(
            path=file_path,
            filename=f"multitrack_export_{export_task_id}.wav",
            media_type='audio/wav'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@router.get("/validate/{project_id}")
async def validate_project(project_id: str):
    """
    验证项目数据完整性
    """
    try:
        service = MultitrackService()
        validation_result = await service.validate_project(project_id)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"项目验证失败: {str(e)}")

@router.post("/preview/{project_id}")
async def preview_project_audio(
    project_id: str,
    start_time: float = 0,
    duration: Optional[float] = None
):
    """
    生成项目音频预览，用于实时播放
    """
    try:
        service = MultitrackService()
        result = await service.generate_preview_audio(
            project_id, start_time, duration
        )
        
        if result:
            return {
                "success": True,
                "message": "预览音频生成成功",
                "data": {
                    "preview_file": result["preview_file"],
                    "start_time": start_time,
                    "duration": result["duration"],
                    "sample_rate": result.get("sample_rate", 44100)
                }
            }
        else:
            raise HTTPException(status_code=404, detail="项目不存在或生成失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")

@router.get("/preview/download/{file_id}")
async def download_preview_audio(file_id: str):
    """
    下载预览音频文件
    """
    try:
        file_path = f"outputs/preview_{file_id}.wav"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="预览文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=f"preview_{file_id}.wav",
            media_type='audio/wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}") 