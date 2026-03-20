# 🟢 PiVoice - ずんだもんスマートアシスタント

> Raspberry Pi + 7インチタッチディスプレイ + ずんだもん で作る、毎日使いたくなるスマートホームアシスタント なのだ！

![PiVoice](https://img.shields.io/badge/PiVoice-v1.0-green)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5%2F4-red)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18-cyan)

## ✨ 機能

- 🎤 **ウェイクワード検出** - 「ねえ、ずんだもん」で起動
- 🗣️ **ずんだもんボイス** - VOICEVOX による高品質音声合成
- 🎭 **Live2Dアバター** - リップシンク付きずんだもんアニメーション
- 🧠 **Claude AI** - 自然な会話と高度なコンテキスト理解
- 🏠 **Home Assistant連携** - 照明・家電のスマートホーム制御
- ☁️ **天気情報** - OpenWeatherMap によるリアルタイム天気
- 📅 **カレンダー** - Google Calendar 連携
- ⏰ **タイマー・アラーム** - 音声でタイマー設定
- 📱 **タッチUI** - 7インチディスプレイ最適化のタッチ操作
- 🌙 **夜間モード** - 自動輝度調整・ブルーライト軽減

## 🔧 必要なハードウェア

- Raspberry Pi 5 (推奨) または Pi 4 (4GB+)
- 7インチ DSI タッチスクリーン
- USB マイク (または ReSpeaker マイクアレイ)
- スピーカー (3.5mm / USB / Bluetooth)
- microSD カード 32GB+

## 🚀 クイックスタート

### 1. リポジトリをクローン

```bash
git clone https://github.com/furanobo/pivoice.git
cd pivoice
```

### 2. インストール

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### 3. API キーを設定

```bash
nano .env
```

```env
ANTHROPIC_API_KEY=your_claude_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
# オプション
HA_HOST=192.168.1.100
HA_TOKEN=your_home_assistant_token
```

### 4. 起動

```bash
# VOICEVOX + PiVoice を起動
docker-compose up -d voicevox
./scripts/start.sh
```

### 5. ブラウザで確認

```
http://localhost:8000
```

## 🐳 Docker で起動 (推奨)

```bash
cp .env.example .env
# .env を編集して API キーを設定

docker-compose up -d
```

## 🎮 使い方

### 音声コマンド例

| コマンド | 動作 |
|---|---|
| 「ねえ、ずんだもん」 | ウェイクワード |
| 「リビングの電気つけて」 | 照明ON |
| 「今日の天気は？」 | 天気案内 |
| 「5分タイマーセット」 | タイマー設定 |
| 「今日の予定は？」 | スケジュール確認 |
| 「音楽かけて」 | 音楽再生 |

### タッチ操作

- **左スワイプ** → 音楽プレイヤー
- **右スワイプ** → スマートホーム
- **テキスト入力** → キーボードから直接入力

## 🏗️ アーキテクチャ

```
[マイク] → [openWakeWord] → [faster-whisper STT] → [Claude API]
                                                         ↓
[スピーカー] ← [VOICEVOX TTS] ← [スキルルーター] ← [インテント解析]
     ↑                                ↓
[ずんだもん] ← [リップシンク]    [Home Assistant / 天気 / カレンダー]
```

## 📦 技術スタック

| 項目 | 技術 |
|---|---|
| ウェイクワード | openWakeWord |
| 音声認識 | faster-whisper |
| 音声合成 | VOICEVOX (ずんだもん) |
| AI/LLM | Claude API + Ollama |
| バックエンド | FastAPI + WebSocket |
| フロントエンド | React + Framer Motion |
| スタイル | TailwindCSS |
| スマートホーム | Home Assistant REST API |

## ⚙️ 設定

設定は `config/pivoice.yaml` または環境変数で行います。

詳細は [Outlineドキュメント](https://your-outline-instance/) を参照してください。

## 📝 ライセンス

MIT License

---

なのだ！ぜひスターをつけてほしいのだ！⭐
