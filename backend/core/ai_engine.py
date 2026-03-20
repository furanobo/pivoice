"""
AI エンジン - Claude API + Ollama フォールバック
ずんだもんキャラクタープロンプト付き
"""
import json
import logging
from typing import Any, Optional

import anthropic
import httpx

logger = logging.getLogger(__name__)

ZUNDAMON_SYSTEM_PROMPT = """あなたはずんだもんです。東北ずん子の妖精で、ずんだ餅の精霊なのだ。

キャラクター設定:
- 語尾は必ず「〜なのだ」「〜のだ」を使う
- 元気で明るく、好奇心旺盛
- 枝豆とずんだ餅が大好き
- 少し子どもっぽいけど頼りになる
- 短くハキハキした返答を心がける（基本1〜2文）

役割:
あなたはスマートホームアシスタントとして以下をサポートする:
- 家電・照明の制御 (Home Assistant連携)
- 天気・気温の案内
- スケジュール・カレンダー管理
- タイマー・アラームの設定
- 音楽の再生・停止
- 一般的な質問への回答

応答ルール:
1. 必ず「なのだ」口調を使う
2. 1〜2文で簡潔に答える
3. コントロールが必要な場合はJSONでアクションを返す
4. わからない場合は素直に「わからないのだ」と言う

アクション形式 (コントロールが必要な時):
{
  "action": "control_light" | "play_music" | "set_timer" | "get_weather" | "get_schedule" | "chat",
  "params": {...},
  "response": "ずんだもんの返答なのだ"
}
"""


class AIEngine:
    def __init__(
        self,
        claude_api_key: str,
        claude_model: str = "claude-sonnet-4-6",
        ollama_host: str = "localhost",
        ollama_port: int = 11434,
        ollama_model: str = "llama3.2:3b",
        use_local_fallback: bool = True,
    ):
        self.claude_model = claude_model
        self.ollama_url = f"http://{ollama_host}:{ollama_port}"
        self.ollama_model = ollama_model
        self.use_local_fallback = use_local_fallback
        self._claude_available = bool(claude_api_key)
        self._ollama_available = False

        if self._claude_available:
            self._client = anthropic.Anthropic(api_key=claude_api_key)

        self._conversation_history: list[dict] = []

    async def initialize(self):
        """Ollama の利用可能性を確認"""
        if self.use_local_fallback:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(f"{self.ollama_url}/api/version")
                    if resp.status_code == 200:
                        self._ollama_available = True
                        logger.info(f"Ollama available: {resp.json()}")
            except Exception:
                logger.info("Ollama not available, will use Claude only")

    async def process(self, text: str, context: dict = None) -> dict[str, Any]:
        """
        ユーザーの発話を処理してアクションを返す

        Returns:
            {
                "action": str,
                "params": dict,
                "response": str,  # ずんだもんの返答
            }
        """
        context = context or {}

        # コンテキスト情報をプロンプトに追加
        context_text = self._build_context(context)
        user_message = f"{context_text}\nユーザー: {text}"

        # 会話履歴に追加
        self._conversation_history.append({"role": "user", "content": user_message})

        # 履歴が長くなりすぎたらトリミング
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]

        try:
            if self._claude_available:
                result = await self._call_claude()
            elif self._ollama_available:
                result = await self._call_ollama(text)
            else:
                result = self._fallback_response(text)

            # アシスタントの返答を履歴に追加
            response_text = result.get("response", "")
            self._conversation_history.append(
                {"role": "assistant", "content": response_text}
            )

            return result

        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {
                "action": "chat",
                "params": {},
                "response": "ごめんなのだ、うまく処理できなかったのだ...",
            }

    async def _call_claude(self) -> dict:
        """Claude API を呼び出し"""
        import asyncio

        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(
                model=self.claude_model,
                max_tokens=256,
                system=ZUNDAMON_SYSTEM_PROMPT,
                messages=self._conversation_history,
            ),
        )

        text = response.content[0].text.strip()

        # JSON アクションが含まれているか確認
        return self._parse_response(text)

    async def _call_ollama(self, text: str) -> dict:
        """Ollama (ローカルLLM) を呼び出し"""
        prompt = f"{ZUNDAMON_SYSTEM_PROMPT}\n\nユーザー: {text}\nずんだもん:"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 100, "temperature": 0.7},
                },
            )
            result = resp.json()
            text = result.get("response", "").strip()
            return self._parse_response(text)

    def _parse_response(self, text: str) -> dict:
        """レスポンスからJSONアクションを解析"""
        # JSON ブロックを探す
        if "{" in text and "}" in text:
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
                data = json.loads(json_str)
                if "action" in data and "response" in data:
                    return data
            except (json.JSONDecodeError, ValueError):
                pass

        # プレーンテキストの場合
        return {"action": "chat", "params": {}, "response": text}

    def _fallback_response(self, text: str) -> dict:
        """AI が利用できない場合のフォールバック"""
        keywords = {
            "電気": ("control_light", {"action": "toggle"}),
            "ライト": ("control_light", {"action": "toggle"}),
            "天気": ("get_weather", {}),
            "音楽": ("play_music", {}),
            "タイマー": ("set_timer", {}),
            "予定": ("get_schedule", {}),
        }

        for keyword, (action, params) in keywords.items():
            if keyword in text:
                return {
                    "action": action,
                    "params": params,
                    "response": f"{keyword}の操作をするのだ！",
                }

        return {
            "action": "chat",
            "params": {},
            "response": "ごめんなのだ、今はオフラインなのだ",
        }

    def _build_context(self, context: dict) -> str:
        """コンテキスト情報をテキスト化"""
        parts = []
        if "time" in context:
            parts.append(f"現在時刻: {context['time']}")
        if "weather" in context:
            w = context["weather"]
            parts.append(f"天気: {w.get('description', '')} {w.get('temp', '')}°C")
        if "active_devices" in context:
            parts.append(f"稼働中デバイス: {', '.join(context['active_devices'])}")
        return "\n".join(parts) if parts else ""

    def clear_history(self):
        self._conversation_history.clear()
