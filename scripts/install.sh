#!/bin/bash
# PiVoice インストールスクリプト
# Raspberry Pi OS (64bit) 対応

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔═══════════════════════════════════╗"
echo "║  PiVoice インストーラー なのだ！  ║"
echo "║  🟢 ずんだもんアシスタント        ║"
echo "╚═══════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ======================================
# システム依存関係
# ======================================
echo -e "${BLUE}📦 システムパッケージをインストールするのだ...${NC}"
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    libportaudio2 \
    ffmpeg \
    espeak-ng \
    nodejs \
    npm \
    chromium-browser \
    git \
    curl \
    docker.io \
    docker-compose

# Docker グループに追加
sudo usermod -aG docker $USER

# ======================================
# Python 仮想環境
# ======================================
echo -e "${BLUE}🐍 Python 仮想環境を作成するのだ...${NC}"
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip wheel
pip install -r requirements.txt

# ======================================
# VOICEVOX エンジン (Docker)
# ======================================
echo -e "${BLUE}🎤 VOICEVOX エンジンをセットアップするのだ...${NC}"

# ARM64 向け VOICEVOX
docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest 2>/dev/null || \
    echo -e "${YELLOW}⚠️  VOICEVOXのDockerイメージ取得に失敗。手動で設定してください${NC}"

# ======================================
# フロントエンド
# ======================================
echo -e "${BLUE}⚛️  フロントエンドをビルドするのだ...${NC}"
cd "$PROJECT_DIR/frontend"
npm install
npm run build
cd "$PROJECT_DIR"

# ======================================
# 環境変数ファイル
# ======================================
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}📝 .env ファイルを作成するのだ...${NC}"
    cat > "$PROJECT_DIR/.env" << 'EOF'
# PiVoice 環境変数
# 必須: Claude API Key
ANTHROPIC_API_KEY=your_claude_api_key_here

# オプション: 天気情報
OPENWEATHER_API_KEY=your_openweather_api_key_here

# オプション: Home Assistant
# HA_HOST=192.168.1.100
# HA_TOKEN=your_ha_long_lived_token_here
EOF
    echo -e "${YELLOW}⚠️  .env ファイルに API キーを設定してください！${NC}"
fi

# ======================================
# systemd サービス
# ======================================
echo -e "${BLUE}🔧 systemd サービスを設定するのだ...${NC}"
sudo tee /etc/systemd/system/pivoice.service > /dev/null << EOF
[Unit]
Description=PiVoice ずんだもんアシスタント
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/pivoice-voicevox.service > /dev/null << 'EOF'
[Unit]
Description=VOICEVOX Engine
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/bin/docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
ExecStop=/usr/bin/docker stop voicevox
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pivoice-voicevox
sudo systemctl enable pivoice

# ======================================
# Chromium 自動起動 (キオスクモード)
# ======================================
echo -e "${BLUE}🖥️  ディスプレイを設定するのだ...${NC}"
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/pivoice-display.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=PiVoice Display
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run http://localhost:8000
X-GNOME-Autostart-enabled=true
EOF

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════╗"
echo "║  ✅ インストール完了なのだ！              ║"
echo "║                                           ║"
echo "║  次のステップ:                            ║"
echo "║  1. .env に API キーを設定するのだ        ║"
echo "║  2. sudo systemctl start pivoice-voicevox ║"
echo "║  3. sudo systemctl start pivoice          ║"
echo "║  4. http://localhost:8000 を開くのだ      ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"
