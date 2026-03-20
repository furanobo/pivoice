"""OpenWeatherMap API クライアント"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherClient:
    def __init__(self, api_key: str, city: str = "Tokyo", language: str = "ja"):
        self.api_key = api_key
        self.city = city
        self.language = language
        self._cache: Optional[dict] = None
        self._cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=30)

    async def get_current(self) -> dict:
        """現在の天気を取得 (キャッシュ付き)"""
        if self._cache and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_duration:
                return self._cache

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/weather",
                params={
                    "q": self.city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": self.language,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        result = {
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "city": data["name"],
            "wind_speed": data["wind"]["speed"],
        }

        self._cache = result
        self._cache_time = datetime.now()
        return result

    async def get_forecast(self, days: int = 3) -> list[dict]:
        """天気予報を取得"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/forecast",
                params={
                    "q": self.city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": self.language,
                    "cnt": days * 8,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        # 1日1件に集約
        daily: dict[str, dict] = {}
        for item in data["list"]:
            date = item["dt_txt"][:10]
            if date not in daily:
                daily[date] = {
                    "date": date,
                    "temp_max": item["main"]["temp_max"],
                    "temp_min": item["main"]["temp_min"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                }
            else:
                daily[date]["temp_max"] = max(
                    daily[date]["temp_max"], item["main"]["temp_max"]
                )
                daily[date]["temp_min"] = min(
                    daily[date]["temp_min"], item["main"]["temp_min"]
                )

        return list(daily.values())[:days]
