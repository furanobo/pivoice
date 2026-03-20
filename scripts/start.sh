#!/bin/bash
# PiVoice 起動スクリプト

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# .env 読み込み
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# VOICEVOX が起動していなければ起動
if ! curl -s http://localhost:50021/version > /dev/null 2>&1; then
    echo "🎤 VOICEVOX を起動するのだ..."
    docker run -d --name voicevox -p 50021:50021 \
        voicevox/voicevox_engine:cpu-ubuntu20.04-latest 2>/dev/null || \
        docker start voicevox 2>/dev/null || \
        echo "⚠️  VOICEVOX の起動に失敗しました"
    sleep 5
fi

# Python venv 有効化
source venv/bin/activate

echo "🟢 PiVoice を起動するのだ！"
uvicorn backend.api.main:app \
    --host "${PIVOICE_HOST:-0.0.0.0}" \
    --port "${PIVOICE_PORT:-8000}" \
    --workers 1
