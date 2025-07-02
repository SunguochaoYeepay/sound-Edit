# 🎵 Sound-Edit | 多轨音频编辑器

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/SunguochaoYeepay/sound-Edit)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-red.svg)](https://fastapi.tiangolo.com/)

一个现代化的多轨音频编辑器，支持拖拽式编辑、实时预览、音频分类管理等功能。基于 Vue3 + FastAPI 构建，提供专业级的音频编辑体验。

## ✨ 核心功能

### 🎛️ 多轨音频编辑
- **拖拽式界面**：直观的音频片段拖拽操作
- **多轨支持**：支持对话、环境音、主题音三种音轨类型
- **精确时间控制**：毫秒级音频定位和编辑
- **实时预览**：即时播放和效果预览

### 🎵 音频处理能力
- **智能分类**：音频文件自动分类管理（对话/环境音/主题音）
- **格式支持**：支持 WAV、MP3、FLAC 等主流音频格式
- **音频特效**：音量调节、淡入淡出、音频增强
- **导出功能**：高质量音频导出，支持多种格式

### 🎮 用户体验
- **键盘快捷键**：空格键播放/暂停，Delete键删除，Escape清除选择
- **响应式设计**：适配不同屏幕尺寸，充分利用屏幕空间
- **智能UI**：动态信息面板，根据选择状态显示不同内容
- **批量操作**：支持多选删除、批量导入等批量操作

### 💾 项目管理
- **项目保存**：完整的项目状态持久化
- **数据库集成**：SQLite数据库存储音频文件信息
- **文件关联**：音频文件与项目的智能关联管理

## 🚀 技术架构

### 前端技术栈
- **Vue 3** - 现代化前端框架
- **Ant Design Vue 4.x** - 企业级UI组件库
- **Vite** - 快速构建工具
- **JavaScript ES6+** - 现代JavaScript语法

### 后端技术栈
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - Python ORM框架
- **SQLite** - 轻量级关系数据库
- **FFmpeg** - 音频处理引擎
- **Celery** - 异步任务队列（预留）

### 部署架构
- **Docker** - 容器化部署
- **Nginx** - 反向代理（可选）
- **跨平台支持** - Windows、macOS、Linux

## 📦 快速开始

### 环境要求
- Node.js >= 16.0
- Python >= 3.8
- FFmpeg（音频处理）

### 1. 克隆项目
```bash
git clone https://github.com/SunguochaoYeepay/sound-Edit.git
cd sound-Edit
```

### 2. 后端服务启动
```bash
cd backend
# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m app.main
```

### 3. 前端应用启动
```bash
cd frontend
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用
- 🌐 **前端界面**：http://localhost:5173
- 🔌 **后端API**：http://localhost:8000  
- 📚 **API文档**：http://localhost:8000/docs

## 🔧 开发指南

### 项目结构
```
sound-Edit/
├── backend/                # 后端服务
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── models.py      # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 应用入口
│   ├── requirements.txt   # Python依赖
│   └── Dockerfile        # Docker配置
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── api/          # API接口
│   │   └── utils/        # 工具函数
│   ├── package.json      # Node依赖
│   └── vite.config.js    # Vite配置
├── docs/                 # 项目文档
├── docker/              # Docker配置
└── README.md           # 项目说明
```

### API 接口

#### 音频文件管理
- `POST /api/v1/audio-files/upload` - 单文件上传
- `POST /api/v1/audio-files/upload/multiple` - 批量上传  
- `GET /api/v1/audio-files/list` - 文件列表
- `GET /api/v1/audio-files/info/{file_id}` - 文件详情
- `DELETE /api/v1/audio-files/{file_id}` - 删除文件

#### 多轨项目管理
- `POST /api/v1/multitrack-projects/` - 创建项目
- `GET /api/v1/multitrack-projects/{project_id}` - 获取项目
- `PUT /api/v1/multitrack-projects/{project_id}` - 更新项目
- `DELETE /api/v1/multitrack-projects/{project_id}` - 删除项目

#### 音频编辑
- `POST /api/v1/audio-editor/preview` - 生成预览
- `POST /api/v1/audio-editor/export` - 导出音频
- `DELETE /api/v1/audio-editor/preview/{filename}` - 清理预览

### 开发规范
- **代码风格**：使用 ESLint + Prettier
- **提交规范**：遵循 Conventional Commits
- **分支策略**：main 分支为稳定版本
- **测试覆盖**：关键功能需要单元测试

## 🎯 使用场景

### 🎬 影视制作
- 对话音轨与背景音乐的精确混合
- 环境音效的层次化编排
- 音频时间轴的精确控制

### 🎙️ 播客制作  
- 多人对话的音轨分离编辑
- 背景音乐的智能淡入淡出
- 音频质量的后期优化

### 🎵 音乐创作
- 多乐器音轨的分层编辑
- 音频样本的创意拼接
- 实验性音效的制作

### 📱 应用开发
- 应用音效的批量制作
- 游戏背景音乐的动态编排
- 交互音频的精确时间控制

## 📝 更新日志

查看完整的 [更新日志](changlog.md) 了解项目最新进展。

### 最新版本 v1.0.0 (2025-01-07)
- ✨ 完整的多轨音频编辑功能
- 🎵 数据库集成与音频分类系统
- ⌨️ 键盘快捷键支持
- 🎛️ 响应式布局优化
- 🐛 播放稳定性修复

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 报告问题
- 使用 [Issues](https://github.com/SunguochaoYeepay/sound-Edit/issues) 报告bug
- 提供详细的复现步骤和环境信息

### 提交代码
1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 开发环境
- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

## 🔗 相关链接

- 📋 [项目看板](https://github.com/SunguochaoYeepay/sound-Edit/projects)
- 🐛 [问题反馈](https://github.com/SunguochaoYeepay/sound-Edit/issues)
- 📖 [开发文档](docs/)
- 🚀 [版本发布](https://github.com/SunguochaoYeepay/sound-Edit/releases)

## ⭐ 支持项目

如果这个项目对您有帮助，请给它一个 ⭐ Star！

---

<div align="center">
  <p>🎵 <strong>Sound-Edit</strong> - 让音频编辑更简单，让创作更自由</p>
  <p>Made with ❤️ by <a href="https://github.com/SunguochaoYeepay">SunguochaoYeepay</a></p>
</div>