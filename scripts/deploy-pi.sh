#!/bin/bash
# PiVoice Pi エッジクライアントセットアップ
# Raspberry Pi 上で実行するスクリプト

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# サーバーアドレス (Proxmox CT120)
PIVOICE_SERVER="http://192.168.100.113:8000"
PIVOICE_WS="ws://192.168.100.113:8000/ws"

echo -e "${GREEN}"
echo "╔══════════════════════════════════════╗"
echo "║  PiVoice Pi エッジセットアップ なのだ！ ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ======================================
# システム依存関係
# ======================================
echo -e "${BLUE}📦 システムパッケージ...${NC}"
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip python3-venv \
    portaudio19-dev libportaudio2 \
    ffmpeg nodejs npm chromium-browser git curl

# ======================================
# Python 仮想環境 (軽量: 音声処理のみ)
# ======================================
echo -e "${BLUE}🐍 Pi用 Python 環境 (音声処理のみ)...${NC}"
cd "$PROJECT_DIR"
python3 -m venv venv-edge
source venv-edge/bin/activate
pip install --quiet \
    pyaudio sounddevice soundfile numpy \
    openwakeword faster-whisper \
    httpx websockets python-dotenv

# ======================================
# Pi エッジクライアント設定
# ======================================
cat > "$PROJECT_DIR/config/pivoice-edge.yaml" << EOF
# Pi エッジクライアント設定
mode: edge

# 接続先 Proxmox サーバー
edge:
  server_url: "${PIVOICE_SERVER}"
  ws_url: "${PIVOICE_WS}"

# ウェイクワード
wake_word:
  threshold: 0.5
  silence_duration: 1.5

# STT (Pi側で実行)
stt:
  model: tiny            # Pi4はtiny推奨
  language: ja
  device: cpu
  compute_type: int8

# 音声設定
audio:
  sample_rate: 16000
  channels: 1
  volume: 0.8
EOF

# ======================================
# Pi エッジエージェント
# ======================================
cat > "$PROJECT_DIR/pivoice-edge.py" << 'PYEOF'
"""
PiVoice エッジエージェント
Pi側で動作: ウェイクワード → STT → サーバーに送信 → TTS再生
"""
import asyncio
import httpx
import websockets
import json
import sounddevice as sd
import soundfile as sf
import io
import logging
import numpy as np
import pyaudio

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('pivoice-edge')

SERVER_URL = "http://192.168.100.113:8000"
WS_URL     = "ws://192.168.100.113:8000/ws"

SAMPLE_RATE = 16000
CHUNK_SIZE  = 1280
SILENCE_THRESHOLD = 500
SILENCE_DURATION  = 1.5


async def record_audio() -> bytes:
    """VAD付き録音"""
    logger.info("Recording...")
    p = pyaudio.PyAudio()
    stream = p.open(rate=SAMPLE_RATE, channels=1, format=pyaudio.paInt16,
                    input=True, frames_per_buffer=CHUNK_SIZE)
    frames = []
    silent = 0
    has_speech = False
    max_silent = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)
    for _ in range(int(15 * SAMPLE_RATE / CHUNK_SIZE)):
        chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        frames.append(chunk)
        rms = np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(float)**2))
        if rms > SILENCE_THRESHOLD:
            silent = 0; has_speech = True
        else:
            silent += 1
        if has_speech and silent >= max_silent:
            break
    stream.stop_stream(); stream.close(); p.terminate()
    return b"".join(frames)


async def transcribe(audio_bytes: bytes) -> str:
    """faster-whisper で音声をテキストに変換"""
    from faster_whisper import WhisperModel
    if not hasattr(transcribe, '_model'):
        logger.info("Loading Whisper model...")
        transcribe._model = WhisperModel("tiny", device="cpu", compute_type="int8")

    audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    segments, _ = transcribe._model.transcribe(audio_array, language="ja", vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()


async def play_tts(text: str):
    """サーバーのVOICEVOXでTTS生成して再生"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{SERVER_URL}/api/voice/tts", json={"text": text})
        if resp.status_code == 200:
            audio_buf = io.BytesIO(resp.content)
            data, sr = sf.read(audio_buf)
            sd.play(data, sr)
            sd.wait()


async def main():
    """メインループ"""
    logger.info("PiVoice Edge Agent starting... なのだ！")
    logger.info(f"Server: {SERVER_URL}")

    try:
        from openwakeword.model import Model
        ww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        logger.info("Wake word model loaded")
    except Exception as e:
        logger.warning(f"Wake word model failed: {e}. Using energy-based detection.")
        ww_model = None

    p = pyaudio.PyAudio()
    stream = p.open(rate=SAMPLE_RATE, channels=1, format=pyaudio.paInt16,
                    input=True, frames_per_buffer=CHUNK_SIZE)

    logger.info("Listening for wake word...")

    async with websockets.connect(WS_URL) as ws:
        logger.info("WebSocket connected to server")

        async def recv_loop():
            async for msg in ws:
                d = json.loads(msg)
                if d.get("type") == "response" and d.get("text"):
                    await play_tts(d["text"])

        asyncio.create_task(recv_loop())

        while True:
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_array = np.frombuffer(chunk, dtype=np.int16)

            detected = False
            if ww_model:
                pred = ww_model.predict(audio_array)
                detected = any(v > 0.5 for v in pred.values())
            else:
                detected = np.sqrt(np.mean(audio_array.astype(float)**2)) > 3000

            if detected:
                logger.info("Wake word detected!")
                await ws.send(json.dumps({"type": "state", "state": "wake"}))

                audio_bytes = await record_audio()
                text = await transcribe(audio_bytes)
                logger.info(f"Transcribed: '{text}'")

                if text:
                    await ws.send(json.dumps({"type": "text_input", "text": text}))

            await asyncio.sleep(0)

PYEOF

chmod +x "$PROJECT_DIR/pivoice-edge.py"

# ======================================
# フロントエンドビルド
# ======================================
echo -e "${BLUE}⚛️  フロントエンドビルド...${NC}"
cd "$PROJECT_DIR/frontend"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# ======================================
# Chromium 自動起動
# ======================================
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/pivoice.desktop << EOF
[Desktop Entry]
Type=Application
Name=PiVoice Display
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run ${PIVOICE_SERVER}
X-GNOME-Autostart-enabled=true
EOF

# ======================================
# systemd サービス
# ======================================
sudo tee /etc/systemd/system/pivoice-edge.service > /dev/null << EOF
[Unit]
Description=PiVoice Edge Agent
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv-edge/bin/python $PROJECT_DIR/pivoice-edge.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pivoice-edge

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ Pi エッジセットアップ完了なのだ！    ║"
echo "║                                          ║"
echo "║  sudo systemctl start pivoice-edge       ║"
echo "║  UI: ${PIVOICE_SERVER}                   ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
