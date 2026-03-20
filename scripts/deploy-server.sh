#!/bin/bash
# PiVoice サーバーサイドデプロイスクリプト
# Proxmox CT120 (192.168.100.113) へデプロイ

set -e

PIVOICE_CT=120
PIVOICE_IP="192.168.100.113"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🟢 PiVoice サーバーサイドをデプロイするのだ！"
echo "   Proxmox CT${PIVOICE_CT} (${PIVOICE_IP})"

# CT120 にコードをコピー
echo "📦 コードを CT${PIVOICE_CT} にコピーするのだ..."
pct exec $PIVOICE_CT -- mkdir -p /opt/pivoice/{backend,config}

# バックエンドファイルをコピー
for dir in backend config; do
    tar -C "$PROJECT_DIR" -czf - "$dir" | \
        pct exec $PIVOICE_CT -- tar -C /opt/pivoice -xzf -
done

# 依存関係インストール
echo "🐍 依存関係をインストールするのだ..."
pct exec $PIVOICE_CT -- bash -c "
cd /opt/pivoice
/opt/pivoice-venv/bin/pip install --quiet \
  fastapi uvicorn[standard] httpx pyyaml anthropic \
  websockets python-dotenv numpy soundfile 2>&1 | tail -3
echo 'Dependencies installed'
"

# systemd サービス設定
echo "🔧 systemd サービスを設定するのだ..."
pct exec $PIVOICE_CT -- bash -c "
cat > /etc/systemd/system/pivoice.service << 'EOF'
[Unit]
Description=PiVoice API Server (ずんだもん)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/pivoice
EnvironmentFile=-/opt/pivoice/.env
ExecStart=/opt/pivoice-venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pivoice
systemctl restart pivoice
sleep 2
systemctl status pivoice --no-pager
"

echo ""
echo "✅ デプロイ完了なのだ！"
echo "   PiVoice API: http://${PIVOICE_IP}:8000"
echo "   API Status: http://${PIVOICE_IP}:8000/api/status"
