import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ping():
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json()["msg"] == "pong"

def test_mix_audio():
    # 这里只做接口存在性测试，具体业务后续补充
    payload = {
        "tracks": [
            {"file_path": "test1.wav", "start_time": 0, "end_time": 5, "volume": 1.0},
            {"file_path": "test2.wav", "start_time": 2, "end_time": 7, "volume": 0.8}
        ],
        "output_format": "wav"
    }
    resp = client.post("/api/v1/audio-editor/mix", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] in ["pending", "success"]
