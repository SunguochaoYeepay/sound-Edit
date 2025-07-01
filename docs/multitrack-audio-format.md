# 多音轨音频标准JSON格式

## 概述
专为多角色小说朗读设计的音轨数据格式，支持角色对话、环境音效、背景音乐的多轨合成。

## 完整格式示例

```json
{
  "project": {
    "id": "novel_xiyangjixiyouji_chapter01",
    "title": "《西游记》第一回 - 灵根育孕源流出",
    "description": "多角色小说朗读音频合成项目",
    "totalDuration": 1800.5,
    "sampleRate": 44100,
    "channels": 2,
    "exportFormat": "wav",
    "createdAt": "2025-01-07T10:30:00Z",
    "version": "1.0"
  },
  "tracks": [
    {
      "id": "track_dialogue",
      "name": "角色对话",
      "type": "dialogue",
      "volume": 1.0,
      "muted": false,
      "solo": false,
      "color": "#4CAF50",
      "order": 1,
      "clips": [
        {
          "id": "clip_narrator_001",
          "filePath": "/audio/generated/narrator_intro.wav",
          "startTime": 0.0,
          "duration": 15.2,
          "volume": 1.0,
          "fadeIn": 0.5,
          "fadeOut": 0.3,
          "playbackRate": 1.0,
          "character": {
            "name": "旁白",
            "voice": "narrator_male_deep",
            "color": "#2196F3",
            "avatar": "/avatars/narrator.png"
          },
          "text": "话说天下大势，分久必合，合久必分。周末七国分争，并入于秦。",
          "metadata": {
            "emotion": "neutral",
            "chapter": 1,
            "scene": "opening",
            "paragraph": 1
          }
        },
        {
          "id": "clip_sunwukong_001", 
          "filePath": "/audio/generated/sunwukong_birth.wav",
          "startTime": 120.5,
          "duration": 8.3,
          "volume": 1.0,
          "fadeIn": 0.2,
          "fadeOut": 0.2,
          "playbackRate": 1.0,
          "character": {
            "name": "孙悟空",
            "voice": "male_young_energetic",
            "color": "#FF9800",
            "avatar": "/avatars/sunwukong.png"
          },
          "text": "我今日才得出世，就拜谢天地厚德！",
          "metadata": {
            "emotion": "excited",
            "chapter": 1,
            "scene": "birth",
            "paragraph": 15
          }
        }
      ]
    },
    {
      "id": "track_environment",
      "name": "环境音效", 
      "type": "environment",
      "volume": 0.6,
      "muted": false,
      "solo": false,
      "color": "#8BC34A",
      "order": 2,
      "clips": [
        {
          "id": "clip_mountain_wind",
          "filePath": "/audio/environment/mountain_wind.wav",
          "startTime": 0.0,
          "duration": 180.0,
          "volume": 0.4,
          "fadeIn": 2.0,
          "fadeOut": 2.0,
          "playbackRate": 1.0,
          "loop": true,
          "metadata": {
            "scene": "huaguo_mountain",
            "weather": "windy",
            "timeOfDay": "dawn"
          }
        },
        {
          "id": "clip_stone_crack",
          "filePath": "/audio/effects/stone_crack.wav", 
          "startTime": 118.0,
          "duration": 5.2,
          "volume": 0.8,
          "fadeIn": 0.1,
          "fadeOut": 0.5,
          "playbackRate": 1.0,
          "metadata": {
            "scene": "stone_birth",
            "effect": "dramatic"
          }
        }
      ]
    },
    {
      "id": "track_background",
      "name": "背景音乐",
      "type": "background", 
      "volume": 0.3,
      "muted": false,
      "solo": false,
      "color": "#9C27B0",
      "order": 3,
      "clips": [
        {
          "id": "clip_ancient_melody",
          "filePath": "/audio/background/ancient_chinese_melody.wav",
          "startTime": 0.0,
          "duration": 1800.5,
          "volume": 0.25,
          "fadeIn": 3.0,
          "fadeOut": 5.0,
          "playbackRate": 1.0,
          "loop": true,
          "metadata": {
            "genre": "traditional_chinese",
            "mood": "mysterious",
            "instruments": ["guqin", "flute", "bells"]
          }
        }
      ]
    }
  ],
  "markers": [
    {
      "id": "marker_chapter_start",
      "time": 0.0,
      "label": "第一回开始",
      "color": "#F44336"
    },
    {
      "id": "marker_birth_scene", 
      "time": 115.0,
      "label": "孙悟空出世",
      "color": "#FF9800"
    }
  ]
}
```

## 字段说明

### project (项目信息)
- `id`: 项目唯一标识
- `title`: 项目标题
- `description`: 项目描述
- `totalDuration`: 总时长（秒）
- `sampleRate`: 采样率
- `channels`: 声道数
- `exportFormat`: 导出格式
- `createdAt`: 创建时间
- `version`: 格式版本

### tracks (音轨列表)
- `id`: 轨道唯一标识
- `name`: 轨道名称
- `type`: 轨道类型 (`dialogue` | `environment` | `background`)
- `volume`: 轨道整体音量 (0.0-1.0)
- `muted`: 是否静音
- `solo`: 是否独奏
- `color`: 轨道颜色（用于UI显示）
- `order`: 轨道排序
- `clips`: 音频片段列表

### clips (音频片段)
- `id`: 片段唯一标识
- `filePath`: 音频文件路径
- `startTime`: 开始时间（秒）
- `duration`: 持续时间（秒）
- `volume`: 片段音量 (0.0-1.0)
- `fadeIn`: 淡入时长（秒）
- `fadeOut`: 淡出时长（秒）
- `playbackRate`: 播放速度 (0.5-2.0)
- `loop`: 是否循环播放（可选）
- `character`: 角色信息（对话轨专用）
- `text`: 原始文本内容
- `metadata`: 扩展元数据

### character (角色信息)
- `name`: 角色名称
- `voice`: 语音模型标识
- `color`: 角色颜色
- `avatar`: 角色头像路径

### markers (时间标记)
- `id`: 标记唯一标识
- `time`: 时间点（秒）
- `label`: 标记标签
- `color`: 标记颜色

## 转换适配器

为方便将现有的角色对话JSON和环境音JSON转换为此标准格式，提供以下转换接口：

```javascript
// 转换角色对话JSON
function convertDialogueJSON(dialogueData) {
  // 实现转换逻辑
}

// 转换环境音JSON  
function convertEnvironmentJSON(environmentData) {
  // 实现转换逻辑
}

// 合并为标准格式
function mergeToStandardFormat(dialogueData, environmentData, backgroundMusic) {
  // 实现合并逻辑
}
```

## 使用场景

1. **前端展示**: 根据此JSON渲染多轨时间轴界面
2. **编辑功能**: 修改时间、音量、角色等参数
3. **后端处理**: 生成FFmpeg命令进行音频合成
4. **项目管理**: 保存和加载音频项目
5. **格式转换**: 与其他音频编辑软件交换数据 