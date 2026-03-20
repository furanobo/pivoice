"""Home Assistant REST API クライアント"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    def __init__(self, host: str, port: int, token: str):
        self.base_url = f"http://{host}:{port}/api"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_states(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/states", headers=self.headers, timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()

    async def get_state(self, entity_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/states/{entity_id}",
                headers=self.headers,
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def call_service(
        self, domain: str, service: str, data: dict[str, Any] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/services/{domain}/{service}",
                headers=self.headers,
                json=data or {},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
