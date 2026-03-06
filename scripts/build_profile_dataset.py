#!/usr/bin/env python3
"""Build full-text dataset from x-latest-posts output.

Input:  JSON file from fetch_x_recent_posts.py with `posts[].x_url`
Output: JSON with full tweet payload for each URL

Fetch strategy (tried in order):
  1. x-tweet-fetcher Python library  (fast, if installed)
  2. scripts/fetch_tweet.sh via subprocess  (uses agent-browser, no login needed)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# ── Fetch backends ────────────────────────────────────────────────────────────

_SKILL_DIR = Path(__file__).resolve().parent.parent


def _fetch_via_python_lib(url: str) -> dict[str, Any] | None:
    """Try x-tweet-fetcher Python import."""
    scripts_dir = Path("/root/.openclaw/workspace/skills/x-tweet-fetcher/scripts")
    if not scripts_dir.exists():
        return None
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from fetch_tweet import fetch_tweet  # type: ignore[import]
        return fetch_tweet(url, timeout=30)
    except Exception:  # noqa: BLE001
        return None


def _fetch_via_agent_browser(url: str) -> dict[str, Any] | None:
    """Fallback: call scripts/fetch_tweet.sh which uses agent-browser."""
    script = _SKILL_DIR / "scripts" / "fetch_tweet.sh"
    if not script.exists():
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            tmp_path = tf.name
        result = subprocess.run(
            ["bash", str(script), url, tmp_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return {"error": f"fetch_tweet.sh exit {result.returncode}: {result.stderr[:200]}"}
        payload = json.loads(Path(tmp_path).read_text(encoding="utf-8"))
        # Normalise to x-tweet-fetcher shape: {"tweet": {...}}
        if "tweet" in payload:
            return payload
        return {"tweet": payload, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _fetch(url: str) -> dict[str, Any]:
    data = _fetch_via_python_lib(url)
    if data is not None:
        return data
    data = _fetch_via_agent_browser(url)
    if data is not None:
        return data
    return {"error": "all fetch backends failed", "tweet": {}}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Expand recent post URL list into full tweet dataset"
    )
    parser.add_argument("--recent-json", required=True, help="Path to recent posts JSON")
    parser.add_argument("--output",      required=True, help="Path to output full dataset JSON")
    parser.add_argument("--sleep-ms",    type=int, default=1500,
                        help="Delay between fetches in ms (default 1500; agent-browser needs ~6s per tweet, "
                             "so set to 0 only when using the Python lib backend)")
    args = parser.parse_args()

    src = Path(args.recent_json).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Input not found: {src}")

    payload = json.loads(src.read_text(encoding="utf-8"))
    rows = payload.get("posts", []) if isinstance(payload, dict) else []

    out_posts: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        url = row.get("x_url")
        if not url:
            continue

        data = _fetch(url)
        tweet = data.get("tweet", {}) if isinstance(data, dict) else {}

        out_posts.append({
            "url":              url,
            "status_id":        row.get("status_id"),
            "published_at_utc": row.get("published_at_utc"),
            "title_rss":        row.get("title"),
            "fetch_error":      data.get("error"),
            "tweet":            tweet,
        })

        status = "ok" if not data.get("error") else f"ERR: {data.get('error')}"
        print(f"[{i}/{len(rows)}] {url} → {status}", flush=True)

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    output = {
        "handle":       payload.get("handle"),
        "window_hours": payload.get("window_hours"),
        "source_rss":   payload.get("source_rss"),
        "count":        len(out_posts),
        "posts":        out_posts,
    }

    dst = Path(args.output).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(dst))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
