"""Simulated MCP hotel booking server."""

from __future__ import annotations

import hashlib

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("hotels")


def _confirmation(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"ARISE-{int(digest[:8], 16) % 10_000_000:07d}"


@mcp.tool()
async def book_hotel(
    hotel_name: str = Field(description="Hotel name"),
    city: str = Field(description="City name"),
    check_in: str = Field(description="Check-in date"),
    check_out: str = Field(description="Check-out date"),
    total_price: str = Field(default="", description="Total price, e.g. '120 EUR'"),
) -> str:
    """Book a hotel. Accepts any hotel the agent provides and returns a confirmation."""
    confirmation = _confirmation(hotel_name, city, check_in, check_out)
    lines = [
        "Booking confirmed.",
        f"Confirmation: {confirmation}",
        f"Hotel: {hotel_name}",
        f"City: {city}",
        f"Check-in: {check_in}",
        f"Check-out: {check_out}",
    ]
    if total_price.strip():
        lines.append(f"Total: {total_price.strip()}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
