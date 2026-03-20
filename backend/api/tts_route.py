"""TTS エンドポイント - Pi エッジクライアント用
WAV音声データを直接返す (Pi側で再生)
"""
import logging
from fastapi import APIRouter
from fastapi.responses import Response

logger = logging.getLogger(__name__)
router = APIRouter()


def get_tts():
    """TTS インスタンスを取得 (循環インポート回避)"""
    from backend.api.main import tts
    return tts


@router.post("/api/voice/tts")
async def tts_endpoint(body: dict):
    """テキストからWAV音声データを生成して返す"""
    text = body.get("text", "").strip()
    if not text:
        return Response(status_code=400)

    tts = get_tts()
    if tts is None:
        return Response(status_code=503)

    audio_data = await tts.synthesize(text)
    if audio_data is None:
        return Response(status_code=503)

    return Response(content=audio_data, media_type="audio/wav")
