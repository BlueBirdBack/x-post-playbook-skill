#!/usr/bin/env python3
"""Convert an X post dump (json/txt) into a concise execution playbook.

Usage:
  python3 scripts/post_to_playbook.py \
    --input /path/to/post.json \
    --url https://x.com/user/status/123 \
    --output /path/to/playbook.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


# ── Source loading ────────────────────────────────────────────────────────────

def _load_source(path: Path) -> tuple[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() != ".json":
        return text.strip(), {}

    payload = json.loads(text)

    # Common structures: fetch_tweet.sh / x-tweet-fetcher / fxtwitter API wrappers
    tweet = payload.get("tweet", {}) if isinstance(payload, dict) else {}
    nested_tweet = payload.get("data", {}).get("tweet", {}) if isinstance(payload, dict) else {}

    body = (
        tweet.get("text")
        or nested_tweet.get("text")
        or payload.get("text")
        or ""
    )

    stats = {
        "likes":    tweet.get("likes")         if isinstance(tweet, dict) else None,
        "retweets": tweet.get("retweets")       if isinstance(tweet, dict) else None,
        "views":    tweet.get("views")          if isinstance(tweet, dict) else None,
        "replies":  tweet.get("replies_count")  if isinstance(tweet, dict) else payload.get("reply_count"),
        "author":   tweet.get("screen_name")    if isinstance(tweet, dict) else None,
    }

    return str(body).strip(), stats


# ── Content type detection ────────────────────────────────────────────────────

_COMMERCE_KW = (
    "sell", "sold", "selling", "buy", "bought", "price", "cost", "profit",
    "revenue", "flip", "listing", "auction", "offer", "deal", "discount",
    "register", "registration", "domain", "afternic", "dan.com", "godaddy",
    "namecheap", "porkbun", "sav", "spaceship", "namesilo", "escrow",
    "卖", "买", "出售", "域名", "注册", "花费", "收入", "赚", "变现",
    "$", "¥", "€", "£",
)
_WORKFLOW_KW = (
    "step", "how to", "process", "workflow", "pipeline", "script",
    "automat", "deploy", "cron", "agent", "prompt", "template",
    "流程", "步骤", "如何", "自动", "调度", "脚本", "部署", "提示词",
)
_ANNOUNCE_KW = (
    "launch", "launched", "ship", "shipped", "release", "released",
    "introducing", "just dropped", "announcing", "new:",
    "发布", "上线", "推出", "发了", "正式", "开源", "上架",
)


def _detect_content_type(text: str) -> str:
    t = text.lower()
    if any(k in t for k in _COMMERCE_KW):
        return "commerce"
    if any(k in t for k in _ANNOUNCE_KW):
        return "announcement"
    if text.rstrip().endswith("?") or re.search(r"\b(why|how|what|when|who|which)\b", t):
        return "question"
    if any(k in t for k in _WORKFLOW_KW):
        return "workflow"
    return "opinion"


# ── Number extraction ─────────────────────────────────────────────────────────

def _extract_numbers(text: str) -> list[str]:
    found: list[str] = []
    # Prices: $4.99, $1,488, $50k, ¥200
    for m in re.finditer(r"[\$¥€£][\d,]+(?:\.\d+)?(?:[km]b?)?", text, re.I):
        found.append(m.group())
    # Percentages
    for m in re.finditer(r"\d+(?:\.\d+)?\s*%", text):
        found.append(m.group())
    # Durations: "4 months", "7 days", "48h", "2 years"
    for m in re.finditer(r"\d+\s*(?:months?|days?|years?|weeks?|hours?|hrs?|h\b)", text, re.I):
        found.append(m.group().strip())
    # Multipliers: 200×, 300x return
    for m in re.finditer(r"\d+\s*[×x]\s*(?:return|cost|profit|roi)?", text, re.I):
        found.append(m.group().strip())
    return list(dict.fromkeys(found))  # dedupe, preserve order


# ── Engagement quality ────────────────────────────────────────────────────────

def _engagement_label(stats: dict[str, Any]) -> str | None:
    likes    = int(stats.get("likes")    or 0)
    views    = int(stats.get("views")    or 0)
    replies  = int(stats.get("replies")  or 0)

    if not views or not likes:
        return None

    rate = likes / views * 1000  # likes per 1k views
    parts: list[str] = []

    if rate >= 20:
        parts.append("🔥 viral")
    elif rate >= 5:
        parts.append("⚡ strong")
    elif rate >= 1:
        parts.append("👍 normal")
    else:
        parts.append("📉 low")

    parts.append(f"{rate:.1f} likes/1k views")

    if likes and replies:
        rr = replies / likes
        if rr > 0.5:
            parts.append("💬 controversy-magnet")
        elif rr < 0.05:
            parts.append("❤️ pure-appreciation")

    return " · ".join(parts)


# ── Why it worked ─────────────────────────────────────────────────────────────

def _why_it_worked(text: str, stats: dict[str, Any], content_type: str) -> list[str]:
    likes    = int(stats.get("likes")    or 0)
    views    = int(stats.get("views")    or 0)
    replies  = int(stats.get("replies")  or 0)
    retweets = int(stats.get("retweets") or 0)
    reasons: list[str] = []

    if content_type == "commerce":
        numbers = _extract_numbers(text)
        if numbers:
            reasons.append(
                f"Concrete numbers ({', '.join(numbers[:4])}) make the claim verifiable at a glance — "
                "readers can immediately judge whether it's worth clicking."
            )
        if len(text.replace("\n", " ")) < 140:
            reasons.append(
                "Short format (< 140 chars): one fact + one context line = "
                "maximum signal density, minimum friction to read and repost."
            )

    if views and likes:
        rate = likes / views * 1000
        if rate >= 5:
            reasons.append(
                f"High engagement rate ({rate:.1f} likes/1k views) suggests emotional resonance — "
                "the audience felt validated or surprised, not just informed."
            )
        if retweets and likes and retweets / likes > 0.1:
            reasons.append(
                "High repost:like ratio — readers shared it as social proof, not just saved it for themselves."
            )

    if replies >= 10:
        reasons.append(
            f"{replies} replies signals a live discussion thread — "
            "the original post acted as a conversation seed, not just a broadcast."
        )

    if not reasons:
        reasons.append(
            "Engagement data unavailable — "
            "assess by asking: does this post make one specific surprising claim with evidence?"
        )

    return reasons


# ── Core thesis ───────────────────────────────────────────────────────────────

def _core_thesis(text: str, content_type: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    if content_type == "commerce":
        # Prefer lines that contain a price or the word "domain"
        for ln in lines:
            if re.search(r"[\$¥€£][\d,]|domain|域名|sell|卖", ln, re.I):
                return ln
    if content_type == "announcement":
        for ln in lines:
            if re.search(r"launch|ship|release|发布|上线|推出", ln, re.I):
                return ln

    for ln in lines:
        if ln.startswith("http"):
            continue
        if re.fullmatch(r"#?[\w\u4e00-\u9fff-]+", ln):
            continue
        return ln

    return "Turn content intake into repeatable execution loops."


# ── Numbered section extraction ───────────────────────────────────────────────

def _extract_numbered_sections(text: str) -> list[str]:
    pattern = re.compile(r"(?:^|\n)\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.)|\Z)", re.S)
    sections: list[str] = []
    for _, raw in pattern.findall(text):
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if cleaned:
            sections.append(cleaned)
    return sections


# ── Content-type-aware workflow steps ─────────────────────────────────────────

_STEPS_BY_TYPE: dict[str, list[str]] = {
    "commerce": [
        "Identify the asset: what is it, what was the acquisition cost, what problem does the name solve?",
        "Find 3 comparable sold/listed prices on Afternic, Dan.com, or Sedo within the same TLD.",
        "List on the highest-traffic marketplace the same day — don't wait.",
        "Set calendar reminders to reprice: -10% at 30d, -20% at 60d, -30% at 90d.",
        "After 6 months with no buyer: drop to cost + 5× or let expire and redeploy capital.",
    ],
    "announcement": [
        "Capture the product URL and put it in your research queue.",
        "Identify the exact problem it solves and who is the target user.",
        "Compare to your current stack — replacement, complement, or ignore?",
        "If worth using: run a 15-minute trial today, not 'later'.",
        "If worth sharing: draft one specific use-case post within 24 hours.",
    ],
    "question": [
        "Restate the question as a testable hypothesis: 'If X, then Y.'",
        "Find 2–3 data points that already bear on the answer.",
        "Design one experiment or conversation that could falsify it.",
        "Run the experiment; record the result regardless of outcome.",
        "Publish your answer as a follow-up post — questions + answers outperform questions alone.",
    ],
    "workflow": [
        "Capture the post as structured text; extract each numbered step verbatim.",
        "Map each step to a concrete tool or command in your stack.",
        "Run the workflow manually once end-to-end before automating.",
        "Automate only the steps that ran cleanly; flag the ones that need human judgment.",
        "Review outputs after 7 days — refine or discard based on actual utility.",
    ],
    "opinion": [
        "Identify the core claim and whether it is empirically testable.",
        "Note where you agree, where you're uncertain, where you disagree — one line each.",
        "Find one concrete action this opinion implies; do it or explicitly reject it.",
        "Write a one-sentence verdict and save it with the source URL for future reference.",
    ],
}


def _short_steps(text: str, content_type: str) -> list[str]:
    # If post has explicit numbered steps, extract and use those first
    sections = _extract_numbered_sections(text)
    if sections:
        steps: list[str] = []
        for block in sections[:5]:
            chunk = re.split(r"[。.!?]\s*", block)[0].strip()
            steps.append(chunk or block[:90].strip())
        return steps
    return _STEPS_BY_TYPE.get(content_type, _STEPS_BY_TYPE["opinion"])


# ── Automation hooks ──────────────────────────────────────────────────────────

def _keyword_hooks(text: str, content_type: str) -> list[str]:
    t = text.lower()
    hooks: list[str] = []

    mapping = [
        # Commerce / domain
        (("domain", "域名", "afternic", "dan.com", "godaddy", "namecheap",
          "porkbun", "sav", "spaceship", "namesilo", ".app", ".io", ".ai"),
         "Register intent-clear domains at promo pricing → list on Afternic/Dan at 100–300× cost the same day; reprice monthly."),
        (("sell", "sold", "卖", "出售", "flip", "listing"),
         "Track every asset you sell: acquisition cost, list price, days-to-sale, buyer source. That data tells you what to buy next."),
        (("register", "注册", "bought", "buy", "purchase", "花费", "promo"),
         "Lock promo-price registrations before first-year discounts expire; log cost + target list price in one spreadsheet row."),
        # Build / ship
        (("launch", "ship", "release", "open source", "发布", "上线", "推出", "开源"),
         "Publish a launch post the moment you ship — early social proof compounds; waiting loses momentum."),
        (("revenue", "mrr", "arr", "paid", "收入", "变现", "赚"),
         "Post revenue milestones publicly — they attract collaborators, press, and customers more than feature lists."),
        # Agents / automation
        (("agent", "subagent", "cron", "automat", "调度", "自动"),
         "Delegate heavy experiments to sub-agents; keep the main flow lightweight and reviewable."),
        (("memory", "记忆", "recall", "召回", "log"),
         "Write key decisions to memory files in real time — mental notes die when the session ends."),
        (("vps", "server", "gateway", "deploy", "部署", "服务器"),
         "Design multi-node fallback channels so one failure doesn't stop the whole workflow."),
        # Content / social
        (("thread", "1/", "🧵", "串"),
         "Threads outperform single tweets for tutorials — break complex ideas into ≤5 posts, each self-contained."),
        (("issue", "github", "pr", "排优先级", "任务"),
         "Convert interesting findings into GitHub issues immediately; a link in chat is forgotten in 24h."),
        (("comment", "reply", "评论", "回复"),
         "Mine comments/replies for edge cases and expert corrections — the real insight is often in the replies."),
    ]

    for keys, sentence in mapping:
        if any(k in t for k in keys):
            hooks.append(sentence)

    # Content-type defaults when no keyword matched
    if not hooks:
        defaults = {
            "commerce": ["Capture cost + ask price for every asset the day you list it.",
                         "Set a 30/60/90-day reprice calendar event at time of listing."],
            "announcement": ["Test the tool today, not tomorrow — first-mover advantage is real.",
                              "Write one sentence on what it does differently before you forget."],
            "question": ["Publish your answer once you have one — your audience asked the same question."],
            "workflow": ["Create one capture-to-action loop: fetch post → extract tactics → assign step.",
                         "Keep a small review loop: summarize what worked and adjust the next run."],
            "opinion": ["State your own view on this opinion in one sentence, then move on."],
        }
        hooks = defaults.get(content_type, defaults["workflow"])

    return hooks


# ── Link extraction ───────────────────────────────────────────────────────────

def _extract_links(text: str) -> list[str]:
    raw_urls = re.findall(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+", text)
    cleaned: list[str] = []
    for url in raw_urls:
        url = re.sub(r"[.,;:!?)\]\}]+$", "", url)
        if url:
            cleaned.append(url)
    return sorted(set(cleaned))


# ── Markdown builder ──────────────────────────────────────────────────────────

def build_markdown(source_url: str, raw_text: str, stats: dict[str, Any]) -> str:
    content_type = _detect_content_type(raw_text)
    thesis       = _core_thesis(raw_text, content_type)
    steps        = _short_steps(raw_text, content_type)
    hooks        = _keyword_hooks(raw_text, content_type)
    links        = _extract_links(raw_text)
    numbers      = _extract_numbers(raw_text)
    eng_label    = _engagement_label(stats)
    why          = _why_it_worked(raw_text, stats, content_type)

    stat_bits: list[str] = []
    for k in ("author", "likes", "retweets", "views", "replies"):
        v = stats.get(k)
        if v is not None and v != "":
            stat_bits.append(f"- {k}: {v}")
    if eng_label:
        stat_bits.append(f"- quality: {eng_label}")

    md: list[str] = []
    md.append("# X Post Playbook\n")

    md.append("## Source")
    md.append(f"- url: {source_url or '(not provided)'}")
    md.append(f"- type: {content_type}")
    md.append("")

    if stat_bits:
        md.append("## Signal snapshot")
        md.extend(stat_bits)
        md.append("")

    if numbers:
        md.append("## Key numbers")
        for n in numbers[:6]:
            md.append(f"- {n}")
        md.append("")

    md.append("## Core thesis")
    md.append(f"- {thesis}")
    md.append("")

    md.append("## Why it worked")
    for r in why:
        md.append(f"- {r}")
    md.append("")

    md.append("## Workflow (actionable)")
    for i, s in enumerate(steps, 1):
        md.append(f"{i}. {s}")
    md.append("")

    md.append("## Automation hooks")
    for h in hooks:
        md.append(f"- {h}")
    md.append("")

    if links:
        md.append("## Referenced links")
        for u in links[:12]:
            md.append(f"- {u}")
        md.append("")

    md.append("## Next step")
    md.append(f"- Pick step **1** above and execute it within 10 minutes.")
    md.append("")

    return "\n".join(md)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Build a concise playbook from X post text/json")
    parser.add_argument("--input",  required=True, help="Path to post .json or .txt")
    parser.add_argument("--url",    default="",    help="Original post URL")
    parser.add_argument("--output", default="",    help="Write markdown to this file (stdout if omitted)")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    raw_text, stats = _load_source(input_path)
    if not raw_text:
        raise SystemExit("No post text found in input")

    md = build_markdown(args.url, raw_text, stats)

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(str(out))
    else:
        print(md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
