import pytest
import asyncio
import json
from datetime import datetime
from app.services.multitrack_service import MultitrackService
from app.services.conversion_service import ConversionService
from app.schemas.multitrack_project import MultitrackProject, ProjectInfo

class TestMultitrackProject:
    """多音轨项目功能测试"""
    
    @pytest.fixture
    def sample_dialogue_data(self):
        """示例对话数据"""
        return {
            "title": "测试小说朗读",
            "dialogues": [
                {
                    "character": "张三",
                    "voice": "voice_001",
                    "text": "你好，今天天气真不错。",
                    "file_path": "/audio/dialogue_001.wav",
                    "start_time": 0.0,
                    "duration": 3.5,
                    "volume": 1.0,
                    "emotion": "happy"
                },
                {
                    "character": "李四",
                    "voice": "voice_002", 
                    "text": "是啊，确实很适合出去走走。",
                    "file_path": "/audio/dialogue_002.wav",
                    "start_time": 4.0,
                    "duration": 4.2,
                    "volume": 1.0,
                    "emotion": "neutral"
                },
                {
                    "character": "张三",
                    "voice": "voice_001",
                    "text": "那我们一起去公园吧！",
                    "file_path": "/audio/dialogue_003.wav",
                    "start_time": 8.5,
                    "duration": 2.8,
                    "volume": 1.0,
                    "emotion": "excited"
                }
            ]
        }
    
    @pytest.fixture
    def sample_environment_data(self):
        """示例环境音数据"""
        return {
            "environments": [
                {
                    "name": "公园鸟鸣",
                    "type": "ambient",
                    "file_path": "/audio/park_birds.wav",
                    "start_time": 0.0,
                    "duration": 15.0,
                    "volume": 0.6,
                    "loop": True,
                    "description": "清晨公园中的鸟鸣声"
                },
                {
                    "name": "脚步声",
                    "type": "effect",
                    "file_path": "/audio/footsteps.wav", 
                    "start_time": 8.0,
                    "duration": 5.0,
                    "volume": 0.4,
                    "loop": False,
                    "description": "走在石径上的脚步声"
                }
            ]
        }
    
    @pytest.fixture
    def sample_background_music(self):
        """示例背景音乐数据"""
        return {
            "name": "轻柔钢琴曲",
            "file_path": "/audio/piano_background.wav",
            "start_time": 0.0,
            "duration": 20.0,
            "volume": 0.3,
            "genre": "classical",
            "mood": "peaceful",
            "loop": True
        }

    @pytest.mark.asyncio
    async def test_format_conversion(self, sample_dialogue_data, sample_environment_data, sample_background_music):
        """测试格式转换功能"""
        conversion_service = ConversionService()
        
        # 执行格式转换
        project = await conversion_service.convert_to_standard_format(
            dialogue_data=sample_dialogue_data,
            environment_data=sample_environment_data,
            background_music=sample_background_music
        )
        
        # 验证项目结构
        assert isinstance(project, MultitrackProject)
        assert project.project.title == "测试小说朗读"
        assert len(project.tracks) == 3
        
        # 验证对话轨道
        dialogue_track = next(track for track in project.tracks if track.type == "dialogue")
        assert dialogue_track.name == "角色对话"
        assert len(dialogue_track.clips) == 3
        assert dialogue_track.clips[0].metadata["character"] == "张三"
        assert dialogue_track.clips[1].metadata["character"] == "李四"
        
        # 验证环境音轨道
        env_track = next(track for track in project.tracks if track.type == "environment")
        assert env_track.name == "环境音效"
        assert len(env_track.clips) == 2
        assert env_track.clips[0].name == "公园鸟鸣"
        
        # 验证背景音乐轨道
        bg_track = next(track for track in project.tracks if track.type == "background")
        assert bg_track.name == "背景音乐"
        assert len(bg_track.clips) == 1
        assert bg_track.clips[0].name == "轻柔钢琴曲"
        
        # 验证时间标记
        assert len(project.markers) >= 1
        assert project.markers[0].name == "开始"
        assert project.markers[0].time == 0.0

    @pytest.mark.asyncio
    async def test_project_crud_operations(self, sample_dialogue_data):
        """测试项目增删改查操作"""
        service = MultitrackService()
        conversion_service = ConversionService()
        
        # 创建项目
        project = await conversion_service.convert_to_standard_format(
            dialogue_data=sample_dialogue_data
        )
        
        created_project = await service.create_project(project)
        project_id = created_project.project.id
        
        # 验证项目创建
        assert project_id is not None
        assert created_project.project.createdAt is not None
        
        # 加载项目
        loaded_project = await service.load_project(project_id)
        assert loaded_project is not None
        assert loaded_project.project.title == "测试小说朗读"
        
        # 修改并保存项目
        loaded_project.project.title = "修改后的标题"
        saved_project = await service.save_project(project_id, loaded_project)
        assert saved_project.project.title == "修改后的标题"
        
        # 验证修改生效
        reloaded_project = await service.load_project(project_id)
        assert reloaded_project.project.title == "修改后的标题"
        
        # 列出项目
        projects_list = await service.list_projects()
        assert len(projects_list) >= 1
        assert any(p.id == project_id for p in projects_list)
        
        # 删除项目
        delete_result = await service.delete_project(project_id)
        assert delete_result is True
        
        # 验证删除
        deleted_project = await service.load_project(project_id)
        assert deleted_project is None

    @pytest.mark.asyncio
    async def test_project_validation(self, sample_dialogue_data):
        """测试项目数据验证"""
        service = MultitrackService()
        conversion_service = ConversionService()
        
        # 创建项目
        project = await conversion_service.convert_to_standard_format(
            dialogue_data=sample_dialogue_data
        )
        created_project = await service.create_project(project)
        project_id = created_project.project.id
        
        # 验证项目
        validation_result = await service.validate_project(project_id)
        
        assert "valid" in validation_result
        assert "errors" in validation_result
        assert "warnings" in validation_result
        
        # 清理
        await service.delete_project(project_id)

    @pytest.mark.asyncio
    async def test_export_workflow(self, sample_dialogue_data):
        """测试导出工作流程"""
        service = MultitrackService()
        conversion_service = ConversionService()
        
        # 创建项目
        project = await conversion_service.convert_to_standard_format(
            dialogue_data=sample_dialogue_data
        )
        created_project = await service.create_project(project)
        project_id = created_project.project.id
        
        # 开始导出
        export_task_id = "test_export_123"
        await service.export_project_audio(project_id, export_task_id)
        
        # 检查导出状态
        status = await service.get_export_status(export_task_id)
        assert status["export_task_id"] == export_task_id
        assert status["status"] in ["processing", "completed", "failed"]
        
        # 清理
        await service.delete_project(project_id)

    def test_character_color_assignment(self):
        """测试角色颜色分配"""
        conversion_service = ConversionService()
        
        # 测试多个角色的颜色分配
        colors = []
        for i in range(10):
            color = conversion_service._get_character_color(i)
            colors.append(color)
        
        # 验证颜色格式
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7
        
        # 验证颜色循环
        assert colors[0] == colors[8]  # 索引0和8应该是同一个颜色

    def test_duration_calculation(self):
        """测试总时长计算"""
        conversion_service = ConversionService()
        
        # 创建模拟轨道数据
        from app.schemas.multitrack_project import Track, AudioClip
        
        tracks = [
            Track(
                id="track1", 
                name="轨道1", 
                type="dialogue",
                color="#000000",
                order=1,
                clips=[
                    AudioClip(id="clip1", name="clip1", filePath="test.wav", startTime=0.0, duration=5.0),
                    AudioClip(id="clip2", name="clip2", filePath="test.wav", startTime=6.0, duration=3.0)
                ]
            ),
            Track(
                id="track2",
                name="轨道2", 
                type="environment",
                color="#000000",
                order=2,
                clips=[
                    AudioClip(id="clip3", name="clip3", filePath="test.wav", startTime=2.0, duration=8.0)
                ]
            )
        ]
        
        total_duration = conversion_service._calculate_total_duration(tracks)
        assert total_duration == 10.0  # max(5.0, 9.0, 10.0) = 10.0

if __name__ == "__main__":
    pytest.main([__file__]) 