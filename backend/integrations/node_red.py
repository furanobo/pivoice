"""Node-RED 連携 - CT117 (192.168.100.117)
スマートホーム自動化トリガー
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NodeRedClient:
    def __init__(self, host: str = "192.168.100.117", port: int = 1880):
        self.base_url = f"http://{host}:{port}"

    async def trigger(self, endpoint: str, data: dict[str, Any] = None) -> dict:
        """Node-RED の HTTP エンドポイントをトリガー"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                json=data or {},
            )
            resp.raise_for_status()
            try:
                return resp.json()
            except Exception:
                return {"status": "ok", "text": resp.text}

    async def morning_routine(self) -> dict:
        """朝のルーティン起動"""
        return await self.trigger("/pivoice/morning")

    async def night_routine(self) -> dict:
        """夜のルーティン起動"""
        return await self.trigger("/pivoice/night")

    async def arrive_home(self) -> dict:
        """帰宅シーン"""
        return await self.trigger("/pivoice/arrive")

    async def leave_home(self) -> dict:
        """外出シーン"""
        return await self.trigger("/pivoice/leave")

    async def custom_scene(self, scene: str) -> dict:
        """カスタムシーン実行"""
        return await self.trigger("/pivoice/scene", {"scene": scene})
