"""PiVoice 設定管理"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

CONFIG_PATH = Path(__file__).parent.parent / "config" / "pivoice.yaml"


@dataclass
class VoicevoxConfig:
    host: str = "localhost"
    port: int = 50021
    speaker_id: int = 3  # ずんだもん ノーマル
    speed_scale: float = 1.1
    intonation_scale: float = 1.2
    cache_enabled: bool = True
    cache_size: int = 100
    preload_phrases: List[str] = field(default_factory=lambda: [
        "はい！なのだ！",
        "呼んだのだ？",
        "なにかご用なのだ？",
        "ちょっと待つのだ...",
        "できたのだ！",
        "おはようなのだ！",
        "おやすみなのだ！",
    ])


@dataclass
class STTConfig:
    model: str = "base"  # tiny/base/small
    language: str = "ja"
    device: str = "cpu"
    compute_type: str = "int8"


@dataclass
class WakeWordConfig:
    model_path: str = "hey_pivoice"
    threshold: float = 0.5
    vad_threshold: float = 0.5
    silence_duration: float = 1.5  # 無音判定時間(秒)


@dataclass
class AIConfig:
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "qwen2.5:3b"  # Qwen2.5-3B: Pi5で4-7tok/s, 最推奨
    use_local_fallback: bool = True


@dataclass
class HomeAssistantConfig:
    host: str = ""
    port: int = 8123
    token: str = ""
    enabled: bool = False


@dataclass
class WeatherConfig:
    api_key: str = ""
    city: str = "Tokyo"
    units: str = "metric"
    language: str = "ja"


@dataclass
class SpotifyConfig:
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8888/callback"
    enabled: bool = False


@dataclass
class GoogleCalendarConfig:
    credentials_path: str = "config/google_credentials.json"
    enabled: bool = False


@dataclass
class DisplayConfig:
    width: int = 1024
    height: int = 600
    brightness: int = 80
    auto_brightness: bool = True
    night_mode_hour: int = 22
    morning_hour: int = 7
    show_zundamon: bool = True
    dark_mode: bool = True


@dataclass
class AudioConfig:
    input_device: Optional[int] = None  # None = default
    output_device: Optional[int] = None
    sample_rate: int = 16000
    channels: int = 1
    volume: float = 0.8


@dataclass
class PiVoiceConfig:
    voicevox: VoicevoxConfig = field(default_factory=VoicevoxConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    home_assistant: HomeAssistantConfig = field(default_factory=HomeAssistantConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    spotify: SpotifyConfig = field(default_factory=SpotifyConfig)
    google_calendar: GoogleCalendarConfig = field(default_factory=GoogleCalendarConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False


def load_config() -> PiVoiceConfig:
    config = PiVoiceConfig()

    # 環境変数から API キーを読み込み
    if key := os.getenv("ANTHROPIC_API_KEY"):
        config.ai.claude_api_key = key
    if key := os.getenv("OPENWEATHER_API_KEY"):
        config.weather.api_key = key
    if key := os.getenv("HA_TOKEN"):
        config.home_assistant.token = key
    if host := os.getenv("HA_HOST"):
        config.home_assistant.host = host
        config.home_assistant.enabled = True

    # YAML設定ファイルを読み込み
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        _apply_yaml(config, data)

    return config


def _apply_yaml(config: PiVoiceConfig, data: dict):
    """YAML データを設定に適用"""
    for section, values in data.items():
        if hasattr(config, section) and isinstance(values, dict):
            obj = getattr(config, section)
            for key, value in values.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)


# グローバル設定インスタンス
config = load_config()
