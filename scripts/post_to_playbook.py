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


def _load_source(path: Path) -> tuple[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() != ".json":
        return text.strip(), {}

    payload = json.loads(text)

    # Common structures from x-tweet-fetcher / fx api wrappers
    tweet = payload.get("tweet", {}) if isinstance(payload, dict) else {}
    nested_tweet = payload.get("data", {}).get("tweet", {}) if isinstance(payload, dict) else {}

    body = (
        tweet.get("text")
        or nested_tweet.get("text")
        or payload.get("text")
        or ""
    )

    stats = {
        "likes": tweet.get("likes") if isinstance(tweet, dict) else None,
        "retweets": tweet.get("retweets") if isinstance(tweet, dict) else None,
        "views": tweet.get("views") if isinstance(tweet, dict) else None,
        "replies": tweet.get("replies_count") if isinstance(tweet, dict) else payload.get("reply_count"),
        "author": tweet.get("screen_name") if isinstance(tweet, dict) else None,
    }

    return str(body).strip(), stats


def _extract_numbered_sections(text: str) -> list[str]:
    # Supports patterns like "1.xxx" across lines
    pattern = re.compile(r"(?:^|\n)\s*(\d+)\.\s*(.+?)(?=(?:\n\s*\d+\.)|\Z)", re.S)
    matches = pattern.findall(text)
    sections: list[str] = []
    for _, raw in matches:
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if cleaned:
            sections.append(cleaned)
    return sections


def _core_thesis(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if ln.startswith("http"):
            continue
        # skip hashtag-only lines
        if re.fullmatch(r"#?[\w\u4e00-\u9fff-]+", ln):
            continue
        return ln
    return "Turn content intake into repeatable execution loops."


def _keyword_hooks(text: str) -> list[str]:
    t = text.lower()
    hooks: list[str] = []

    mapping = [
        (("issue", "github", "排优先级", "任务"), "Push interesting links into an issue queue instead of leaving them in chat."),
        (("评论", "comment", "回复"), "Mine comments/replies for edge cases, expert tips, and hard questions."),
        (("时间线", "timeline", "latest", "mentions", "监控"), "Fetch timeline/mentions continuously so context stays fresh without copy-paste."),
        (("异步", "夜间", "晚上", "下班", "凌晨", "cron", "调度", "自动"), "Run async/offline execution windows (work hours or sleep), then review in one morning batch."),
        (("进化", "soul.md", "agent.md", "无为而治", "信任", "自由", "涌现", "冥想"), "Allow bounded autonomy and add self-reflection logs so behavior improves over time."),
        (("记忆", "memory", "召回", "实时", "log"), "Write key decisions into memory in real time, then use recall checks to close gaps."),
        (("vps", "mac", "路由器", "gateway", "ssh", "通道", "具身"), "Design multi-node fallback channels (VPS/Mac/router) instead of single-path control."),
        (("密码", "api", "泄露", "部署", "反向"), "Use privacy-safe deployment paths that avoid exposing customer credentials."),
        (("文章", "article"), "Support both short posts and long-form article links in one pipeline."),
        (("subagent", "agent"), "Delegate heavy experiments to sub-agents and keep main flow lightweight."),
    ]

    for keys, sentence in mapping:
        if any(k in t for k in keys):
            hooks.append(sentence)

    if not hooks:
        hooks = [
            "Create one capture-to-action loop: fetch post → extract tactics → assign execution step.",
            "Keep a small review loop: summarize what worked and adjust the next run.",
        ]

    return hooks


def _short_steps(text: str) -> list[str]:
    sections = _extract_numbered_sections(text)
    if not sections:
        return [
            "Capture one post or thread and store it as text/json.",
            "Extract concrete tactics (not opinions).",
            "Map each tactic to one executable action.",
            "Review output and refine the loop.",
        ]

    steps: list[str] = []
    for block in sections[:5]:
        # first sentence-ish chunk
        chunk = re.split(r"[。.!?]\s*", block)[0].strip()
        if not chunk:
            chunk = block[:90].strip()
        steps.append(chunk)

    return steps


def _extract_links(text: str) -> list[str]:
    # URL-safe charset based on RFC 3986 reserved/unreserved sets.
    raw_urls = re.findall(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+", text)
    cleaned: list[str] = []

    for url in raw_urls:
        url = re.sub(r"[.,;:!?)\]\}]+$", "", url)
        if url:
            cleaned.append(url)

    return sorted(set(cleaned))


def build_markdown(source_url: str, raw_text: str, stats: dict[str, Any]) -> str:
    thesis = _core_thesis(raw_text)
    steps = _short_steps(raw_text)
    hooks = _keyword_hooks(raw_text)
    links = _extract_links(raw_text)

    stat_bits: list[str] = []
    for k in ("author", "likes", "retweets", "views", "replies"):
        v = stats.get(k)
        if v is not None and v != "":
            stat_bits.append(f"- {k}: {v}")

    md: list[str] = []
    md.append("# X Post Playbook\n")
    md.append("## Source")
    md.append(f"- url: {source_url or '(not provided)'}")
    md.append("")

    if stat_bits:
        md.append("## Signal snapshot")
        md.extend(stat_bits)
        md.append("")

    md.append("## Core thesis")
    md.append(f"- {thesis}")
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
    md.append("- Pick exactly one workflow step above and execute it within 10 minutes.")
    md.append("")

    return "\n".join(md)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a concise playbook from X post text/json")
    parser.add_argument("--input", required=True, help="Path to post .json or .txt")
    parser.add_argument("--url", default="", help="Original post URL")
    parser.add_argument("--output", default="", help="Write markdown to this file")
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
