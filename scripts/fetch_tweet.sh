#!/usr/bin/env bash
# Fetch a single X/Twitter post using agent-browser (vercel-labs/agent-browser).
#
# Usage:
#   bash scripts/fetch_tweet.sh <url> [output.json]
#
# Output: JSON with keys: url, text, author, stats { likes, retweets, views, replies }
# Compatible with post_to_playbook.py --input flag.
#
# Requirements:
#   npm install -g agent-browser && agent-browser install --with-deps
#
# Notes:
#   - Closes any running agent-browser daemon before starting (flags must be set at launch)
#   - Waits 6s for X's JS to hydrate
#   - Falls back to snapshot-based text if article selector fails

set -euo pipefail

URL="${1:?Usage: bash scripts/fetch_tweet.sh <url> [output.json]}"
OUTPUT="${2:-}"

# ── 1. Launch browser with correct flags ────────────────────────────────────
agent-browser close 2>/dev/null || true
sleep 0.5

agent-browser open "$URL" \
  --ignore-https-errors \
  --args "--no-sandbox,--disable-dev-shm-usage" 2>/dev/null

sleep 6   # wait for React hydration

# ── 2. Extract tweet text ────────────────────────────────────────────────────
# Primary: article selector that X uses for tweet cards
TEXT=$(agent-browser get text "article[data-testid='tweet']" 2>/dev/null || echo "")

# Fallback: snapshot accessibility tree
SNAPSHOT=$(agent-browser snapshot 2>/dev/null || echo "")

# ── 3. Parse into structured JSON ────────────────────────────────────────────
JSON=$(python3 - "$URL" "$TEXT" "$SNAPSHOT" <<'PY'
import sys, re, json

url      = sys.argv[1]
text_raw = sys.argv[2]
snapshot = sys.argv[3]

# -- Author from @handle in snapshot article line or raw text
author_match = re.search(r'@([A-Za-z0-9_]+)', text_raw or snapshot)
author = author_match.group(1) if author_match else ""

# -- Stats from accessibility tree article description
# Format: "HANDLE Verified account @handle <body> N replies, N reposts, N likes, N bookmarks, N views"
article_match = re.search(r'article "(.+?)"', snapshot, re.S)
article_desc  = article_match.group(1) if article_match else ""

def _num(pattern, text):
    m = re.search(pattern, text, re.I)
    return int(m.group(1).replace(",", "")) if m else None

likes    = _num(r"(\d[\d,]*)\s*likes?",    article_desc)
replies  = _num(r"(\d[\d,]*)\s*repl",      article_desc)
retweets = _num(r"(\d[\d,]*)\s*repost",    article_desc)
views    = _num(r"(\d[\d,]*)\s*views?",    article_desc)

# -- Clean tweet body from raw text
# agent-browser get text may return everything on one line or multi-line.
# Strategy: strip known header (@handle) and footer (Translate post / timestamp / stats).
body = text_raw

# 1. Strip leading "NAME@handle" prefix (e.g. "BECOOL@becool_me")
#    Use ASCII-only pattern for @handle to avoid eating CJK word chars
body = re.sub(r"^[\w\s]+@[A-Za-z0-9_]+\s*", "", body).strip()

# 2. Strip trailing footer starting at "Translate post", timestamp, or view count
body = re.sub(r"\s*Translate\s+post\s*.*$", "", body, flags=re.I | re.S).strip()
body = re.sub(r"\s*\d+:\d+\s*[AP]M\s*[·•].*$", "", body, flags=re.I | re.S).strip()
body = re.sub(r"\s*[\d,]+\s*Views?.*$", "", body, flags=re.I | re.S).strip()
body = re.sub(r"\s*Read\s+\d+\s+repl.*$", "", body, flags=re.I | re.S).strip()

# 3. If body still empty after stripping, fall back to article_desc
if not body and article_desc:
    body = re.sub(r"^[\w\s]+ @\w+\s+", "", article_desc)
    body = re.sub(r"\s+\d[\d,]* repl.*$", "", body, flags=re.I).strip()

result = {
    "tweet": {
        "text":          body,
        "screen_name":   author,
        "likes":         likes,
        "retweets":      retweets,
        "views":         views,
        "replies_count": replies,
    },
    "url": url,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
PY
)

# ── 4. Output ────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT" ]]; then
    echo "$JSON" > "$OUTPUT"
    echo "Saved: $OUTPUT" >&2
else
    echo "$JSON"
fi
