from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.api.v1 import audio_editor, multitrack_project, audio_files


app = FastAPI(title="sound-Edit 多轨音频合成服务")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(audio_editor.router, prefix="/api/v1/audio-editor", tags=["AudioEditor"])
app.include_router(multitrack_project.router, prefix="/api/v1/multitrack", tags=["MultitrackProject"])
app.include_router(audio_files.router, prefix="/api/v1/audio-files", tags=["AudioFiles"])

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true"
    })

@app.get("/ping")
def ping():
    return {"msg": "pong"}
