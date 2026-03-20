"""
スキルルーター - アクションを適切なスキルに振り分け
"""
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from backend.core.tts import ZundamonTTS
    from backend.config import PiVoiceConfig

logger = logging.getLogger(__name__)


class SkillRouter:
    def __init__(self, config: "PiVoiceConfig", tts: "ZundamonTTS", ws_manager: Any):
        self.config = config
        self.tts = tts
        self.ws_manager = ws_manager
        self._weather_cache: Optional[dict] = None
        self._weather_cache_time: Optional[datetime] = None
        self._timers: list[dict] = []

        # スキル初期化
        self._init_skills()

    def _init_skills(self):
        """各スキルモジュールを初期化"""
        self._home_assistant = None
        if self.config.home_assistant.enabled:
            try:
                from backend.integrations.home_assistant import HomeAssistantClient
                self._home_assistant = HomeAssistantClient(
                    host=self.config.home_assistant.host,
                    port=self.config.home_assistant.port,
                    token=self.config.home_assistant.token,
                )
                logger.info("Home Assistant integration enabled")
            except Exception as e:
                logger.warning(f"Home Assistant init failed: {e}")

        self._weather_client = None
        if self.config.weather.api_key:
            try:
                from backend.integrations.weather import WeatherClient
                self._weather_client = WeatherClient(
                    api_key=self.config.weather.api_key,
                    city=self.config.weather.city,
                    language=self.config.weather.language,
                )
                logger.info("Weather integration enabled")
            except Exception as e:
                logger.warning(f"Weather init failed: {e}")

    async def execute(self, action: str, params: dict, response_text: str):
        """アクションを実行して応答を返す"""
        handlers = {
            "control_light": self._handle_light,
            "play_music": self._handle_music,
            "stop_music": self._handle_stop_music,
            "set_timer": self._handle_timer,
            "get_weather": self._handle_weather,
            "get_schedule": self._handle_schedule,
            "chat": self._handle_chat,
        }

        handler = handlers.get(action, self._handle_chat)

        try:
            result_text = await handler(params, response_text)
        except Exception as e:
            logger.error(f"Skill execution error ({action}): {e}")
            result_text = "ごめんなのだ、エラーが起きたのだ"

        # 最終的な返答を読み上げ
        if result_text:
            frames = await self.tts.speak(result_text)
            await self.ws_manager.send_lip_sync(frames)
            await self.ws_manager.send_response(result_text, action)

    async def _handle_light(self, params: dict, response_text: str) -> str:
        """照明制御"""
        if self._home_assistant:
            entity_id = params.get("entity_id", "light.living_room")
            action = params.get("action", "toggle")
            await self._home_assistant.call_service(
                "light", action, {"entity_id": entity_id}
            )
        return response_text or "電気を操作したのだ！"

    async def _handle_music(self, params: dict, response_text: str) -> str:
        """音楽再生"""
        # TODO: Spotify/mopidy 連携
        return response_text or "音楽を再生するのだ！"

    async def _handle_stop_music(self, params: dict, response_text: str) -> str:
        """音楽停止"""
        return response_text or "音楽を止めたのだ！"

    async def _handle_timer(self, params: dict, response_text: str) -> str:
        """タイマー設定"""
        import asyncio

        minutes = params.get("minutes", 0)
        seconds = params.get("seconds", 0)
        total_seconds = int(minutes) * 60 + int(seconds)

        if total_seconds <= 0:
            return "タイマーの時間を教えるのだ！"

        # タイマーをバックグラウンドで実行
        asyncio.create_task(self._run_timer(total_seconds))

        return response_text or f"{minutes}分のタイマーをセットしたのだ！"

    async def _run_timer(self, seconds: int):
        """タイマー実行"""
        import asyncio

        await asyncio.sleep(seconds)
        frames = await self.tts.speak("タイマーが終わったのだ！")
        await self.ws_manager.send_lip_sync(frames)
        await self.ws_manager.send_state("timer_done")

    async def _handle_weather(self, params: dict, response_text: str) -> str:
        """天気情報"""
        if self._weather_client:
            try:
                weather = await self._weather_client.get_current()
                return (
                    f"{weather['description']}なのだ！"
                    f"気温は{weather['temp']}度なのだ！"
                )
            except Exception as e:
                logger.error(f"Weather error: {e}")

        return response_text or "今は天気情報を取得できないのだ"

    async def _handle_schedule(self, params: dict, response_text: str) -> str:
        """スケジュール確認"""
        # TODO: Google Calendar 連携
        return response_text or "今日の予定を確認するのだ！"

    async def _handle_chat(self, params: dict, response_text: str) -> str:
        """一般会話"""
        return response_text

    async def get_context(self) -> dict:
        """現在のコンテキスト情報を取得"""
        context = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        if self._weather_client:
            try:
                weather = await self._weather_client.get_current()
                context["weather"] = weather
            except Exception:
                pass

        if self._home_assistant:
            try:
                devices = await self._home_assistant.get_states()
                active = [d["entity_id"] for d in devices if d.get("state") == "on"]
                context["active_devices"] = active[:5]
            except Exception:
                pass

        return context

    async def get_weather(self) -> dict:
        if self._weather_client:
            return await self._weather_client.get_current()
        return {}

    async def get_calendar(self) -> dict:
        return {"events": [], "message": "カレンダー連携未設定なのだ"}

    async def get_devices(self) -> dict:
        if self._home_assistant:
            states = await self._home_assistant.get_states()
            return {"devices": states}
        return {"devices": [], "message": "Home Assistant未設定なのだ"}

    async def control_device(self, entity_id: str, action: str, params: dict) -> dict:
        if self._home_assistant:
            domain = entity_id.split(".")[0]
            await self._home_assistant.call_service(domain, action, {"entity_id": entity_id, **params})
            return {"success": True}
        return {"success": False, "error": "Home Assistant未設定なのだ"}
