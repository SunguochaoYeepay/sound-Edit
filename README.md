# sound-Edit

多轨音频合成服务（独立开发，后续集成AI-Sound主项目）

## 项目目标
- 提供高性能、可扩展的多轨音频合成API服务
- 支持异步任务、音频特效、波形可视化
- 技术栈与主项目保持一致，便于后续迁移

## 技术栈
- 后端：FastAPI + SQLAlchemy（预留）+ Celery + FFmpeg
- 前端：Vue3 + Ant Design Vue+ wavesurfer.js

## 目录结构
- backend/  后端服务
- frontend/ 前端工程
- docs/     方案与文档
- docker/   容器化相关

## 快速开始
详见 docs/solution.md

---

> 本项目为AI-Sound多轨音频合成模块的独立孵化仓库，开发完成后将整体迁移至主项目。
