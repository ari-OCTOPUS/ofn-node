from __future__ import annotations

from typing import Any


# Owner-stated season place. Not GPS. Not geoip. No invented lat/long.
OWNER_SEASON = {
    "city": "Sydney",
    "region": "NSW",
    "country": "Australia",
    "season": "2026-H2",
    "source": "OWNER_STATED",
    "gps": "ABSENT",
    "geo_coordinates": "UNMEASURED_NO_GPS_NO_GEOIP",
    "claimed_timezone": "Australia/Sydney",
    "note": "Owner said this season the child lives in Sydney NSW. Board clock remains UTC until measured otherwise.",
}


def season_view() -> dict[str, Any]:
    return dict(OWNER_SEASON)


def attach_season(place: dict[str, Any]) -> dict[str, Any]:
    merged = dict(place or {})
    season = season_view()
    merged["owner_city"] = season["city"]
    merged["owner_region"] = season["region"]
    merged["owner_country"] = season["country"]
    merged["owner_season"] = season["season"]
    merged["owner_source"] = season["source"]
    merged["claimed_timezone"] = season["claimed_timezone"]
    return merged
