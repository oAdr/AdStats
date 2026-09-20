#!/usr/bin/env python3
"""Stateless public reference for the AdStats Hypixel lookup path.

This file deliberately has no persistence layer: it writes no files, database,
cache, telemetry, or log. The production QQ gateway is kept on the operator's
server; this reference only demonstrates the read-only API request contract.
"""

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


VERSION = "1.0.0-public-reference"
PLAYER_NAME = re.compile(r"^[A-Za-z0-9_]{1,16}$")
UUID_HEX = re.compile(r"^[0-9a-fA-F]{32}$")
KEY_SHAPE = re.compile(r"^[A-Za-z0-9_-]{16,200}$")
MAX_BODY = 2_000_000


class PublicApiError(Exception):
    def __init__(self, category):
        super().__init__(category)
        self.category = category


def get_json(url, headers):
    """Fetch bounded JSON without retaining a response outside this call."""
    request = Request(url, method="GET", headers={
        "User-Agent": "AdStats-public-reference/1.0",
        "Cache-Control": "no-cache, no-store",
        **headers,
    })
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise PublicApiError("http_status")
            body = response.read(MAX_BODY + 1)
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise PublicApiError("key_rejected") from None
        if exc.code == 404:
            raise PublicApiError("not_found") from None
        if exc.code == 429:
            raise PublicApiError("rate_limited") from None
        raise PublicApiError("http_status") from None
    except (URLError, TimeoutError, OSError):
        raise PublicApiError("network") from None
    if len(body) > MAX_BODY:
        raise PublicApiError("response_too_large")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise PublicApiError("invalid_json") from None
    if not isinstance(value, dict):
        raise PublicApiError("invalid_json")
    return value


def resolve_uuid(name):
    if not PLAYER_NAME.fullmatch(name):
        raise PublicApiError("invalid_player_name")
    data = get_json(
        "https://api.mojang.com/users/profiles/minecraft/" + quote(name, safe=""),
        {},
    )
    if str(data.get("name", "")).casefold() != name.casefold():
        raise PublicApiError("identity_mismatch")
    player_uuid = data.get("id")
    if not isinstance(player_uuid, str) or not UUID_HEX.fullmatch(player_uuid):
        raise PublicApiError("invalid_uuid")
    return player_uuid.lower()


def hypixel_summary(name, player_uuid, key):
    data = get_json(
        "https://api.hypixel.net/v2/player?uuid=" + player_uuid,
        {"API-Key": key},
    )
    if data.get("success") is not True:
        raise PublicApiError("hypixel_api_error")
    player = data.get("player")
    if not isinstance(player, dict):
        return {"name": name, "uuid": player_uuid, "player_found": False}
    stats = player.get("stats")
    available = []
    if isinstance(stats, dict):
        for key_name, label in (("Bedwars", "BedWars"), ("SkyWars", "SkyWars"), ("Duels", "Duels")):
            if isinstance(stats.get(key_name), dict):
                available.append(label)
    rank = player.get("rank") or player.get("monthlyPackageRank") or player.get("newPackageRank")
    return {
        "name": name,
        "uuid": player_uuid,
        "player_found": True,
        "rank": rank if isinstance(rank, str) else None,
        "available_stat_sections": available,
    }


def main(argv):
    if argv[1:] == ["--version"]:
        print(VERSION)
        return 0
    if len(argv) != 2 or not PLAYER_NAME.fullmatch(argv[1]):
        print("usage: adstats_public_bot.py <minecraft-username>", file=sys.stderr)
        return 2
    key = os.environ.get("HYPIXEL_API_KEY", "").strip()
    if not KEY_SHAPE.fullmatch(key):
        print("request_failed:missing_or_invalid_key", file=sys.stderr)
        return 2
    try:
        name = argv[1]
        player_uuid = resolve_uuid(name)
        print(json.dumps(hypixel_summary(name, player_uuid, key), separators=(",", ":")))
        return 0
    except PublicApiError as exc:
        print("request_failed:" + exc.category, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
