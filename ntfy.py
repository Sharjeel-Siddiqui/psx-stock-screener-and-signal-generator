from __future__ import annotations

import requests


def send_ntfy(topic: str, message: str) -> None:
    if not topic:
        raise RuntimeError("NTFY_TOPIC is not configured")

    url = f"https://ntfy.sh/{topic}"

    response = requests.post(
        url,
        data=message.encode("utf-8"),
        headers={
            "Title": "PSX Trading Signal",
            "Priority": "high",
            "Tags": "chart_with_upwards_trend",
        },
        timeout=20,
    )

    response.raise_for_status()

    payload = response.json()

    if not payload.get("id"):
        raise RuntimeError(f"ntfy error: {payload}")