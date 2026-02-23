#!/usr/bin/env python3
"""Build full-text dataset from x-latest-posts output.

Input: JSON file from fetch_x_recent_posts.py with `posts[].x_url`
Output: JSON with full tweet payload for each URL (via fetch_tweet)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand recent post URL list into full tweet dataset")
    parser.add_argument("--recent-json", required=True, help="Path to recent posts JSON")
    parser.add_argument("--output", required=True, help="Path to output full dataset JSON")
    parser.add_argument("--sleep-ms", type=int, default=250, help="Delay between API calls")
    args = parser.parse_args()

    # Local import from sibling skill repo script
    scripts_dir = Path("/root/.openclaw/workspace/skills/x-tweet-fetcher/scripts")
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    try:
        from fetch_tweet import fetch_tweet
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Cannot import fetch_tweet: {exc}")

    src = Path(args.recent_json).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Input not found: {src}")

    payload = json.loads(src.read_text(encoding="utf-8"))
    rows = payload.get("posts", []) if isinstance(payload, dict) else []

    out_posts = []
    for i, row in enumerate(rows, 1):
        url = row.get("x_url")
        if not url:
            continue

        data = fetch_tweet(url, timeout=30)
        out_posts.append(
            {
                "url": url,
                "status_id": row.get("status_id"),
                "published_at_utc": row.get("published_at_utc"),
                "title_rss": row.get("title"),
                "fetch_error": data.get("error"),
                "tweet": data.get("tweet", {}),
            }
        )

        print(
            f"[{i}/{len(rows)}] {url} {'ok' if not data.get('error') else f'ERR: {data.get('error')}'}",
            flush=True,
        )
        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    output = {
        "handle": payload.get("handle"),
        "window_hours": payload.get("window_hours"),
        "source_rss": payload.get("source_rss"),
        "count": len(out_posts),
        "posts": out_posts,
    }

    dst = Path(args.output).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(dst))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
