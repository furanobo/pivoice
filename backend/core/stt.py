"""
音声認識 (STT) - faster-whisper 使用
VAD (音声区間検出) で自動停止
"""
import asyncio
import logging
from typing import Optional

import numpy as np
import pyaudio

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
MAX_RECORD_SECONDS = 15
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5  # 無音がこの秒数続いたら停止


class SpeechRecognizer:
    def __init__(
        self,
        model_size: str = "base",
        language: str = "ja",
        device: str = "cpu",
        compute_type: str = "int8",
        input_device: Optional[int] = None,
    ):
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.input_device = input_device
        self._model = None

    def load_model(self):
        """Whisper モデルを読み込み"""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("faster-whisper not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def record_and_transcribe(self) -> Optional[str]:
        """音声を録音してテキストに変換"""
        logger.info("Recording...")
        audio_data = await self._record_with_vad()

        if audio_data is None or len(audio_data) < SAMPLE_RATE * 0.5:
            logger.warning("Recording too short or empty")
            return None

        return await self._transcribe(audio_data)

    async def _record_with_vad(self) -> Optional[np.ndarray]:
        """VAD付き録音 - 無音で自動停止"""
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(None, self._record_blocking)

    def _record_blocking(self) -> Optional[np.ndarray]:
        """ブロッキング録音処理"""
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self.input_device,
            frames_per_buffer=CHUNK_SIZE,
        )

        frames = []
        silent_chunks = 0
        max_silent_chunks = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)
        max_chunks = int(MAX_RECORD_SECONDS * SAMPLE_RATE / CHUNK_SIZE)
        has_speech = False

        try:
            for _ in range(max_chunks):
                chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                frames.append(chunk)

                # エネルギー計算
                audio_array = np.frombuffer(chunk, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))

                if rms > SILENCE_THRESHOLD:
                    silent_chunks = 0
                    has_speech = True
                else:
                    silent_chunks += 1

                # 音声が始まった後に無音が続いたら停止
                if has_speech and silent_chunks >= max_silent_chunks:
                    logger.info("Silence detected, stopping recording")
                    break

        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

        if not frames:
            return None

        audio_data = np.frombuffer(b"".join(frames), dtype=np.int16)
        return audio_data.astype(np.float32) / 32768.0

    async def _transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Whisper で音声をテキストに変換"""
        if self._model is None:
            logger.error("Whisper model not loaded")
            return None

        loop = asyncio.get_event_loop()

        try:
            segments, info = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    audio_data,
                    language=self.language,
                    beam_size=3,
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 500},
                ),
            )

            text = " ".join(seg.text.strip() for seg in segments)
            text = text.strip()

            logger.info(
                f"Transcribed: '{text}' "
                f"(lang={info.language}, prob={info.language_probability:.2f})"
            )

            return text if text else None

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
