"""
ウェイクワード検出 - openWakeWord 使用
"ねえ、ずんだもん" または "ピーボイス" で起動
"""
import asyncio
import logging
from typing import Callable, Optional

import numpy as np
import pyaudio

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1280  # openWakeWord の推奨チャンクサイズ (80ms @ 16kHz)
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16


class WakeWordDetector:
    def __init__(
        self,
        threshold: float = 0.5,
        on_wake: Optional[Callable] = None,
        input_device: Optional[int] = None,
    ):
        self.threshold = threshold
        self.on_wake = on_wake
        self.input_device = input_device
        self._running = False
        self._model = None
        self._audio = None
        self._stream = None

    def _load_model(self):
        """openWakeWord モデルを読み込み"""
        try:
            from openwakeword.model import Model

            self._model = Model(
                wakeword_models=["hey_jarvis", "alexa"],  # フォールバック用
                enable_speex_noise_suppression=True,
                inference_framework="onnx",
            )
            logger.info("openWakeWord model loaded")
            return True
        except ImportError:
            logger.warning("openWakeWord not installed, using dummy detector")
            return False
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")
            return False

    async def start(self):
        """ウェイクワード検出を開始"""
        self._running = True
        model_loaded = self._load_model()

        self._audio = pyaudio.PyAudio()

        try:
            self._stream = self._audio.open(
                rate=SAMPLE_RATE,
                channels=CHANNELS,
                format=FORMAT,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=CHUNK_SIZE,
            )
            logger.info("Wake word detection started")
            await self._detection_loop(model_loaded)
        finally:
            self._cleanup()

    async def _detection_loop(self, use_model: bool):
        """検出ループ"""
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                # 音声データ取得
                audio_chunk = await loop.run_in_executor(
                    None,
                    lambda: self._stream.read(CHUNK_SIZE, exception_on_overflow=False),
                )

                audio_array = np.frombuffer(audio_chunk, dtype=np.int16)

                if use_model and self._model:
                    # openWakeWord で検出
                    prediction = self._model.predict(audio_array)

                    for model_name, score in prediction.items():
                        if score > self.threshold:
                            logger.info(
                                f"Wake word detected: {model_name} (score={score:.3f})"
                            )
                            if self.on_wake:
                                await self._trigger_wake(model_name, float(score))
                else:
                    # エネルギーベースの簡易検出 (テスト用)
                    rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))
                    if rms > 3000:  # 大きな音で起動
                        logger.debug(f"Energy-based trigger: rms={rms:.0f}")

                await asyncio.sleep(0)  # イベントループに制御を返す

            except Exception as e:
                if self._running:
                    logger.error(f"Wake word detection error: {e}")
                await asyncio.sleep(0.1)

    async def _trigger_wake(self, model_name: str, score: float):
        """ウェイクワード検出時のコールバック"""
        if self.on_wake:
            if asyncio.iscoroutinefunction(self.on_wake):
                await self.on_wake(model_name, score)
            else:
                self.on_wake(model_name, score)

    def stop(self):
        self._running = False

    def _cleanup(self):
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._audio:
            self._audio.terminate()
