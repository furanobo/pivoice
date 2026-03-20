"""
ずんだもん TTS - VOICEVOX エンジン連携
リップシンクデータ生成・キャッシュ対応
"""
import asyncio
import hashlib
import io
import json
import logging
import random
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "tts"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ずんだもんの状態別セリフ
ZUNDAMON_PHRASES = {
    "wake": [
        "はい！なのだ！",
        "呼んだのだ？",
        "なにかご用なのだ？",
        "おっ、どうしたのだ？",
    ],
    "thinking": [
        "うーん、考えてるのだ...",
        "ちょっと待つのだ...",
        "調べてるのだ！",
        "少しだけ待つのだ...",
    ],
    "done": [
        "できたのだ！",
        "完了なのだ！",
        "どうぞなのだ！",
        "お任せなのだ！",
    ],
    "error": [
        "ごめんなさいなのだ...",
        "うまくいかなかったのだ",
        "もう一度試すのだ？",
    ],
    "morning": [
        "おはようなのだ！今日も元気にいくのだ！",
        "いい朝なのだ！頑張るのだ！",
    ],
    "night": [
        "おやすみなのだ！ゆっくり休むのだ！",
        "また明日なのだ！",
    ],
    "not_found": [
        "ごめんなのだ、わからなかったのだ",
        "もう少し詳しく教えるのだ？",
    ],
}


class ZundamonTTS:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50021,
        speaker_id: int = 3,
        speed_scale: float = 1.1,
        intonation_scale: float = 1.2,
        cache_enabled: bool = True,
    ):
        self.base_url = f"http://{host}:{port}"
        self.speaker_id = speaker_id
        self.speed_scale = speed_scale
        self.intonation_scale = intonation_scale
        self.cache_enabled = cache_enabled
        self._cache: dict[str, bytes] = {}
        self._available = False
        self._client = httpx.AsyncClient(timeout=30.0)

    async def initialize(self):
        """VOICEVOX エンジンの接続確認"""
        try:
            resp = await self._client.get(f"{self.base_url}/version")
            if resp.status_code == 200:
                logger.info(f"VOICEVOX engine connected: v{resp.text}")
                self._available = True
            else:
                logger.warning("VOICEVOX engine not available")
        except Exception as e:
            logger.warning(f"VOICEVOX connection failed: {e}")
            self._available = False

    async def synthesize(self, text: str) -> Optional[bytes]:
        """テキストから音声データ(WAV)を生成"""
        if not self._available:
            logger.warning("VOICEVOX not available, skipping TTS")
            return None

        cache_key = self._cache_key(text)

        # キャッシュ確認
        if self.cache_enabled:
            if cache_key in self._cache:
                return self._cache[cache_key]
            cache_file = CACHE_DIR / f"{cache_key}.wav"
            if cache_file.exists():
                data = cache_file.read_bytes()
                self._cache[cache_key] = data
                return data

        try:
            # Step 1: audio_query 生成
            resp = await self._client.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": self.speaker_id},
            )
            resp.raise_for_status()
            query = resp.json()

            # パラメータ調整
            query["speedScale"] = self.speed_scale
            query["intonationScale"] = self.intonation_scale
            query["prePhonemeLength"] = 0.05
            query["postPhonemeLength"] = 0.05

            # Step 2: 音声合成
            resp = await self._client.post(
                f"{self.base_url}/synthesis",
                params={"speaker": self.speaker_id},
                json=query,
            )
            resp.raise_for_status()
            audio_data = resp.content

            # キャッシュ保存
            if self.cache_enabled:
                self._cache[cache_key] = audio_data
                (CACHE_DIR / f"{cache_key}.wav").write_bytes(audio_data)

            return audio_data

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None

    async def speak(self, text: str) -> list[float]:
        """音声を再生し、リップシンクデータを返す"""
        audio_data = await self.synthesize(text)
        if audio_data is None:
            return []

        lip_frames = self._extract_lip_sync(audio_data)

        # 非同期で再生
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._play_audio, audio_data)

        return lip_frames

    def _play_audio(self, audio_data: bytes):
        """WAVデータを再生 (ブロッキング)"""
        try:
            buf = io.BytesIO(audio_data)
            data, samplerate = sf.read(buf)
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def _extract_lip_sync(self, audio_data: bytes, fps: int = 30) -> list[float]:
        """音声データからリップシンク値を抽出 (0.0-1.0)"""
        try:
            buf = io.BytesIO(audio_data)
            audio, sr = sf.read(buf)

            frame_size = sr // fps
            frames = []

            for i in range(0, len(audio), frame_size):
                frame = audio[i : i + frame_size]
                if len(frame) == 0:
                    break
                rms = float(np.sqrt(np.mean(frame**2)))
                lip_value = min(rms * 8.0, 1.0)
                frames.append(round(lip_value, 3))

            return frames
        except Exception as e:
            logger.error(f"Lip sync extraction error: {e}")
            return []

    def get_phrase(self, state: str) -> str:
        """状態に応じたランダムセリフを取得"""
        phrases = ZUNDAMON_PHRASES.get(state, ZUNDAMON_PHRASES["wake"])
        return random.choice(phrases)

    async def speak_state(self, state: str) -> list[float]:
        """状態に応じたセリフを読み上げ"""
        text = self.get_phrase(state)
        return await self.speak(text)

    async def preload_common_phrases(self):
        """よく使うセリフをプリロード"""
        all_phrases = []
        for phrases in ZUNDAMON_PHRASES.values():
            all_phrases.extend(phrases)

        logger.info(f"Preloading {len(all_phrases)} phrases...")
        tasks = [self.synthesize(phrase) for phrase in all_phrases]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Preload complete")

    def _cache_key(self, text: str) -> str:
        key = f"{self.speaker_id}_{self.speed_scale}_{text}"
        return hashlib.md5(key.encode()).hexdigest()

    async def close(self):
        await self._client.aclose()
