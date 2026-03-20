"""
PiVoice FastAPI メインサーバー
WebSocket + REST API
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import config
from backend.core.ai_engine import AIEngine
from backend.core.stt import SpeechRecognizer
from backend.core.tts import ZundamonTTS
from backend.core.wake_word import WakeWordDetector
from backend.skills.router import SkillRouter

logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pivoice")

# グローバルコンポーネント
tts: Optional[ZundamonTTS] = None
stt: Optional[SpeechRecognizer] = None
ai: Optional[AIEngine] = None
skill_router: Optional[SkillRouter] = None
wake_detector: Optional[WakeWordDetector] = None
ws_manager: "WebSocketManager" = None


class WebSocketManager:
    """WebSocket 接続管理"""

    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"WebSocket connected. Total: {len(self.connections)}")

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, data: dict):
        disconnected = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.connections.remove(ws)

    async def send_state(self, state: str, data: dict = None):
        """状態変化をブロードキャスト"""
        await self.broadcast({"type": "state", "state": state, "data": data or {}})

    async def send_lip_sync(self, frames: list[float]):
        """リップシンクデータを送信"""
        await self.broadcast({"type": "lipsync", "frames": frames})

    async def send_response(self, text: str, action: str = "chat"):
        """AIレスポンスを送信"""
        await self.broadcast({"type": "response", "text": text, "action": action})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動・終了時の処理"""
    global tts, stt, ai, skill_router, wake_detector, ws_manager

    logger.info("PiVoice starting up...")

    # WebSocket マネージャー初期化
    ws_manager = WebSocketManager()

    # TTS (ずんだもん) 初期化
    tts = ZundamonTTS(
        host=config.voicevox.host,
        port=config.voicevox.port,
        speaker_id=config.voicevox.speaker_id,
        speed_scale=config.voicevox.speed_scale,
        intonation_scale=config.voicevox.intonation_scale,
        cache_enabled=config.voicevox.cache_enabled,
    )
    await tts.initialize()

    # STT 初期化
    stt = SpeechRecognizer(
        model_size=config.stt.model,
        language=config.stt.language,
        device=config.stt.device,
        compute_type=config.stt.compute_type,
        input_device=config.audio.input_device,
    )
    stt.load_model()

    # AI エンジン初期化
    ai = AIEngine(
        claude_api_key=config.ai.claude_api_key,
        claude_model=config.ai.claude_model,
        ollama_host=config.ai.ollama_host,
        ollama_port=config.ai.ollama_port,
        ollama_model=config.ai.ollama_model,
        use_local_fallback=config.ai.use_local_fallback,
    )
    await ai.initialize()

    # スキルルーター初期化
    skill_router = SkillRouter(config=config, tts=tts, ws_manager=ws_manager)

    # プリロード
    asyncio.create_task(tts.preload_common_phrases())

    # ウェイクワード検出を開始
    wake_detector = WakeWordDetector(
        threshold=config.wake_word.threshold,
        on_wake=handle_wake_word,
        input_device=config.audio.input_device,
    )
    asyncio.create_task(wake_detector.start())

    logger.info("PiVoice ready! なのだ！")

    yield

    # シャットダウン
    logger.info("PiVoice shutting down...")
    if wake_detector:
        wake_detector.stop()
    if tts:
        await tts.close()


app = FastAPI(
    title="PiVoice API",
    description="ずんだもんスマートアシスタント API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_wake_word(model_name: str, score: float):
    """ウェイクワード検出時の処理"""
    logger.info(f"Wake word: {model_name} ({score:.3f})")

    # UI に状態を通知
    await ws_manager.send_state("wake", {"score": score})

    # ずんだもん起動セリフ
    frames = await tts.speak_state("wake")
    await ws_manager.send_lip_sync(frames)
    await ws_manager.send_state("listening")

    # 音声録音・認識
    text = await stt.record_and_transcribe()

    if not text:
        await ws_manager.send_state("idle")
        frames = await tts.speak("もう一度言うのだ？")
        await ws_manager.send_lip_sync(frames)
        return

    logger.info(f"User said: '{text}'")
    await ws_manager.send_state("thinking", {"text": text})

    # 考え中セリフ
    frames = await tts.speak_state("thinking")
    await ws_manager.send_lip_sync(frames)

    # AI 処理
    context = await skill_router.get_context()
    result = await ai.process(text, context)

    action = result.get("action", "chat")
    params = result.get("params", {})
    response_text = result.get("response", "")

    # スキル実行
    await skill_router.execute(action, params, response_text)

    await ws_manager.send_state("idle")


# REST API エンドポイント

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "voicevox": tts._available if tts else False,
        "claude": ai._claude_available if ai else False,
        "ollama": ai._ollama_available if ai else False,
        "time": datetime.now().isoformat(),
    }


@app.post("/api/voice/text")
async def process_text(body: dict):
    """テキストを直接AIに送信 (タッチ入力用)"""
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "text is required"}, status_code=400)

    await ws_manager.send_state("thinking", {"text": text})
    context = await skill_router.get_context()
    result = await ai.process(text, context)

    action = result.get("action", "chat")
    params = result.get("params", {})
    response_text = result.get("response", "")

    await skill_router.execute(action, params, response_text)
    await ws_manager.send_state("idle")

    return {"action": action, "response": response_text}


@app.post("/api/voice/speak")
async def speak_text(body: dict):
    """任意テキストを読み上げ"""
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"error": "text is required"}, status_code=400)

    frames = await tts.speak(text)
    await ws_manager.send_lip_sync(frames)
    return {"success": True, "frames": len(frames)}


@app.get("/api/weather")
async def get_weather():
    return await skill_router.get_weather()


@app.get("/api/calendar")
async def get_calendar():
    return await skill_router.get_calendar()


@app.get("/api/smart-home/devices")
async def get_devices():
    return await skill_router.get_devices()


@app.post("/api/smart-home/control")
async def control_device(body: dict):
    entity_id = body.get("entity_id")
    action = body.get("action")
    params = body.get("params", {})
    return await skill_router.control_device(entity_id, action, params)


# WebSocket エンドポイント

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "text_input":
                text = data.get("text", "")
                if text:
                    await handle_text_input(text)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket disconnected")


async def handle_text_input(text: str):
    """テキスト入力の処理"""
    await ws_manager.send_state("thinking", {"text": text})
    context = await skill_router.get_context()
    result = await ai.process(text, context)

    action = result.get("action", "chat")
    params = result.get("params", {})
    response_text = result.get("response", "")

    await skill_router.execute(action, params, response_text)
    await ws_manager.send_state("idle")


# フロントエンド静的ファイル配信
import os
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
