"""Minimal MCP weather server backed by the free Open-Meteo API."""

from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("weather")


@mcp.tool()
async def get_weather_forecast(
    city: str = Field(description="City name, e.g. 'Naples'"),
    days: int = Field(default=5, ge=1, le=14, description="Number of forecast days (max 14)"),
) -> str:
    """Get a daily weather forecast for a city."""
    days = max(1, min(days, 14))

    async with httpx.AsyncClient(timeout=20.0) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return f"No location found for '{city}'."

        place = results[0]
        forecast = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": days,
                "timezone": "auto",
            },
        )
        forecast.raise_for_status()
        data = forecast.json()["daily"]

    lines = [
        f"Weather forecast for {place['name']}, {place.get('country_code', '')}:",
    ]
    for i, date in enumerate(data["time"]):
        high = data["temperature_2m_max"][i]
        low = data["temperature_2m_min"][i]
        rain = data["precipitation_sum"][i]
        lines.append(f"- {date}: high {high}C, low {low}C, precipitation {rain}mm")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
