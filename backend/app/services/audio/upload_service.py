import os
import uuid
import aiofiles
from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException
from pathlib import Path
from sqlalchemy.orm import Session

from .ffmpeg_service import FFmpegService
from app.models import AudioFile, AudioCategory
from app.database import SessionLocal


class AudioUploadService:
    """
    音频文件上传服务
    """
    
    def __init__(self):
        self.upload_dir = "uploads/audio"
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', 
            '.m4a', '.wma', '.opus', '.aiff'
        }
        self.ffmpeg_service = FFmpegService()
        
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def upload_audio_file(self, file: UploadFile, category: str = "dialogue", project_id: Optional[str] = None) -> Dict:
        """
        上传单个音频文件
        """
        # 验证文件
        self._validate_file(file)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        file_name = f"{file_id}{file_extension}"
        file_path = os.path.join(self.upload_dir, file_name)
        
        db = SessionLocal()
        try:
            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            print(f"文件已保存: {file_path}, 大小: {len(content)} bytes")
            
            # 获取音频信息
            audio_info = await self.ffmpeg_service.get_audio_info(file_path)
            
            # 生成波形数据
            try:
                waveform_data = await self.ffmpeg_service.extract_waveform_data(file_path)
            except Exception as e:
                print(f"波形提取失败: {e}")
                waveform_data = []
            
            # 保存到数据库
            audio_file = AudioFile(
                file_id=file_id,
                original_name=file.filename,
                file_path=file_path,
                category=AudioCategory(category),
                project_id=project_id,
                file_size=len(content),
                duration=audio_info['duration'],
                sample_rate=audio_info['sample_rate'],
                channels=audio_info['channels'],
                format=audio_info['format'],
                codec=audio_info['codec'],
                bitrate=audio_info['bitrate']
            )
            
            db.add(audio_file)
            db.commit()
            db.refresh(audio_file)
            
            result = audio_file.to_dict()
            result.update({
                'waveform_data': waveform_data,
                'upload_success': True
            })
            
            return result
            
        except Exception as e:
            db.rollback()
            # 如果处理失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
        finally:
            db.close()
    
    async def upload_multiple_files(self, files: List[UploadFile], category: str = "dialogue", project_id: Optional[str] = None) -> List[Dict]:
        """
        批量上传音频文件
        """
        results = []
        
        for file in files:
            try:
                result = await self.upload_audio_file(file, category, project_id)
                results.append(result)
            except Exception as e:
                results.append({
                    'original_name': file.filename,
                    'upload_success': False,
                    'error': str(e)
                })
        
        return results
    
    def _validate_file(self, file: UploadFile):
        """
        验证上传的文件
        """
        # 检查文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件扩展名
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_extension}. 支持的格式: {', '.join(self.allowed_extensions)}"
            )
        
        # 检查文件大小（这里只是初步检查，实际大小在读取后验证）
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"文件太大: {file.size} bytes. 最大允许: {self.max_file_size} bytes"
            )
    
    async def get_file_info(self, file_id: str) -> Optional[Dict]:
        """
        获取已上传文件的信息
        """
        # 查找文件
        file_path = None
        for filename in os.listdir(self.upload_dir):
            if filename.startswith(file_id):
                file_path = os.path.join(self.upload_dir, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            return None
        
        try:
            audio_info = await self.ffmpeg_service.get_audio_info(file_path)
            return {
                'file_id': file_id,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                **audio_info
            }
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除上传的文件（同时删除文件和数据库记录）
        """
        db = SessionLocal()
        try:
            # 从数据库获取文件信息
            audio_file = db.query(AudioFile).filter(AudioFile.file_id == file_id).first()
            if not audio_file:
                return False
            
            # 删除物理文件
            if os.path.exists(audio_file.file_path):
                try:
                    os.remove(audio_file.file_path)
                except Exception as e:
                    print(f"删除物理文件失败: {e}")
            
            # 删除数据库记录
            db.delete(audio_file)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"删除文件失败: {e}")
            return False
        finally:
            db.close()
    
    async def list_uploaded_files(self, project_id: Optional[str] = None) -> List[Dict]:
        """
        列出所有已上传的文件（从数据库读取）
        """
        db = SessionLocal()
        try:
            query = db.query(AudioFile)
            if project_id:
                query = query.filter(AudioFile.project_id == project_id)
            
            audio_files = query.order_by(AudioFile.created_at.desc()).all()
            return [file.to_dict() for file in audio_files]
        finally:
            db.close()
    
    async def convert_to_standard_format(self, file_id: str, 
                                       output_format: str = 'wav',
                                       sample_rate: int = 44100) -> Optional[str]:
        """
        将上传的文件转换为标准格式
        """
        # 查找原文件
        source_path = None
        for filename in os.listdir(self.upload_dir):
            if filename.startswith(file_id):
                source_path = os.path.join(self.upload_dir, filename)
                break
        
        if not source_path or not os.path.exists(source_path):
            return None
        
        # 生成输出文件路径
        output_filename = f"{file_id}_converted.{output_format}"
        output_path = os.path.join(self.upload_dir, output_filename)
        
        try:
            await self.ffmpeg_service.convert_audio(
                source_path, output_path, 
                format=output_format, 
                sample_rate=sample_rate
            )
            return output_path
        except Exception as e:
            print(f"音频转换失败: {e}")
            return None