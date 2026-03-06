#!/usr/bin/env python3
"""Mine repeatable execution patterns from a batch of X posts.

Input format: JSON with top-level `posts`, where each item includes:
- url
- tweet.text
- tweet.likes / tweet.views / tweet.retweets

Works with files like: YuLin807-recent-168h-full.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Pattern:
    key: str
    title: str
    summary: str
    keywords: tuple[str, ...]


PATTERNS: tuple[Pattern, ...] = (
    Pattern(
        key="async-night-ops",
        title="Async Night Ops",
        summary="Run tasks while offline (night/work hours), then review outputs in one batch.",
        keywords=("异步", "夜间", "晚上", "下班", "凌晨", "自动", "调度", "cron", "静默", "睡着"),
    ),
    Pattern(
        key="issue-driven-learning",
        title="Issue-Driven Learning",
        summary="Convert content intake into ranked issue queues with clear execution owners.",
        keywords=("issue", "排优先级", "任务", "github", "研究", "安排"),
    ),
    Pattern(
        key="comments-and-timeline-intel",
        title="Comments + Timeline Intel",
        summary="Mine replies/comments/timeline for edge-case tactics and fast context sync.",
        keywords=("评论区", "回复", "时间线", "mentions", "监控", "抓", "latest"),
    ),
    Pattern(
        key="autonomy-and-evolution",
        title="Autonomy + Evolution",
        summary="Grant bounded autonomy, let agent self-reflect, and evolve behavior over time.",
        keywords=("进化", "soul.md", "agent.md", "无为而治", "自由", "信任", "涌现", "冥想", "活着"),
    ),
    Pattern(
        key="memory-first-operations",
        title="Memory-First Operations",
        summary="Use live memory/logging to improve recall and continuity across sessions.",
        keywords=("记忆", "召回", "memory", "log", "evolution-log", "实时"),
    ),
    Pattern(
        key="infra-embodiment",
        title="Infra Embodiment",
        summary="Treat infra as body parts (VPS/Mac/router) with resilient fallback channels.",
        keywords=("vps", "mac", "路由器", "gateway", "bind", "ssh", "通道", "具身"),
    ),
    Pattern(
        key="privacy-safe-deployment",
        title="Privacy-Safe Deployment",
        summary="Design deployment workflows that avoid exposing customer secrets.",
        keywords=("密码", "api", "泄露", "反向", "部署", "顾客", "隐私", "密钥"),
    ),
    Pattern(
        key="build-in-public-recap",
        title="Build-in-Public Recap",
        summary="Publish concrete daily recaps with numbers, fixes, and links to reproducible steps.",
        keywords=("今天 openclaw 帮我干了点啥", "成果", "q&a", "系列", "配图", "地址", "教程"),
    ),
)


def _norm(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load_posts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    posts = payload.get("posts", []) if isinstance(payload, dict) else []
    out: list[dict[str, Any]] = []
    for row in posts:
        tweet = row.get("tweet", {}) if isinstance(row, dict) else {}
        out.append(
            {
                "url": row.get("url", ""),
                "text": tweet.get("text", "") or row.get("title_rss", ""),
                "likes": int(tweet.get("likes") or 0),
                "views": int(tweet.get("views") or 0),
                "retweets": int(tweet.get("retweets") or 0),
            }
        )
    return out


def _score(post: dict[str, Any]) -> int:
    # Lightweight influence score, views-dominant but with social confirmation.
    return int(post.get("views", 0)) + 40 * int(post.get("likes", 0)) + 80 * int(post.get("retweets", 0))


def _detect_patterns(post: dict[str, Any]) -> list[str]:
    t = _norm(post.get("text", ""))
    hits: list[str] = []
    for p in PATTERNS:
        if any(k in t for k in p.keywords):
            hits.append(p.key)
    return hits


def mine(posts: list[dict[str, Any]], top_k: int = 3) -> dict[str, Any]:
    mapping = {p.key: p for p in PATTERNS}
    groups: dict[str, list[dict[str, Any]]] = {p.key: [] for p in PATTERNS}
    unclassified: list[dict[str, Any]] = []

    for post in posts:
        post["score"] = _score(post)
        labels = _detect_patterns(post)
        if not labels:
            unclassified.append(post)
            continue
        for lb in labels:
            groups[lb].append(post)

    pattern_rows: list[dict[str, Any]] = []
    for key, rows in groups.items():
        if not rows:
            continue
        rows_sorted = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
        pattern_rows.append(
            {
                "key": key,
                "title": mapping[key].title,
                "summary": mapping[key].summary,
                "count": len(rows),
                "total_views": sum(int(r.get("views", 0)) for r in rows),
                "avg_views": int(sum(int(r.get("views", 0)) for r in rows) / max(1, len(rows))),
                "examples": rows_sorted[:top_k],
            }
        )

    pattern_rows.sort(key=lambda r: (r["count"], r["total_views"]), reverse=True)

    return {
        "post_count": len(posts),
        "classified_count": len(posts) - len(unclassified),
        "unclassified_count": len(unclassified),
        "patterns": pattern_rows,
        "unclassified": sorted(unclassified, key=lambda r: r.get("score", 0), reverse=True)[:top_k],
    }


def to_markdown(report: dict[str, Any], source_hint: str) -> str:
    lines: list[str] = []
    lines.append("# Profile Pattern Report\n")
    lines.append(f"- source: {source_hint}")
    lines.append(f"- posts analyzed: {report.get('post_count', 0)}")
    lines.append(f"- classified: {report.get('classified_count', 0)}")
    lines.append(f"- unclassified: {report.get('unclassified_count', 0)}")
    lines.append("")

    lines.append("## Dominant patterns")
    for i, p in enumerate(report.get("patterns", []), 1):
        lines.append(f"### {i}. {p['title']} ({p['count']} posts)")
        lines.append(f"- why it matters: {p['summary']}")
        lines.append(f"- signal: total_views={p['total_views']} | avg_views={p['avg_views']}")
        lines.append("- evidence:")
        for ex in p.get("examples", []):
            snippet = _norm(ex.get("text", ""))[:110]
            lines.append(
                f"  - {ex.get('url')}  (views={ex.get('views',0)}, likes={ex.get('likes',0)}, rt={ex.get('retweets',0)})"
            )
            lines.append(f"    - {snippet}")
        lines.append("")

    if report.get("unclassified"):
        lines.append("## Unclassified high-signal posts")
        for ex in report["unclassified"]:
            lines.append(f"- {ex.get('url')} (views={ex.get('views',0)})")
        lines.append("")

    lines.append("## Skill-upgrade suggestions")
    lines.append("- Expand automation hooks beyond single-post parsing: support async-night planning and daily recap patterns.")
    lines.append("- Add profile mining mode to derive recurring patterns from 10–30 recent posts.")
    lines.append("- Keep one safety/guardrail section for autonomy + privacy-sensitive deployment.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine recurring workflow patterns from X post batch JSON")
    parser.add_argument("--input", required=True, help="Path to full posts JSON")
    parser.add_argument("--output", default="", help="Write markdown report to this file")
    parser.add_argument("--json-output", default="", help="Optional structured JSON output path")
    parser.add_argument("--top-k", type=int, default=3, help="Examples per pattern")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    posts = _load_posts(input_path)
    report = mine(posts, top_k=max(1, args.top_k))

    md = to_markdown(report, source_hint=str(input_path))

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(str(out))
    else:
        print(md)

    if args.json_output:
        jout = Path(args.json_output).expanduser().resolve()
        jout.parent.mkdir(parents=True, exist_ok=True)
        jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(jout))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
