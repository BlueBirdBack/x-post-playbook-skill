#!/usr/bin/env python3
"""Mine repeatable execution patterns from a batch of X posts.

Input format: JSON with top-level `posts`, where each item includes:
- url
- tweet.text
- tweet.likes / tweet.views / tweet.retweets / tweet.replies_count

Works with any profile dataset built by build_profile_dataset.py.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ── Pattern registry ──────────────────────────────────────────────────────────

@dataclass
class Pattern:
    key: str
    title: str
    summary: str
    skill_upgrade: str          # concrete action to add to your workflow/skill
    keywords: tuple[str, ...]


PATTERNS: tuple[Pattern, ...] = (
    # ── Agent / automation patterns ───────────────────────────────────────────
    Pattern(
        key="async-night-ops",
        title="Async Night Ops",
        summary="Run tasks while offline (night/work hours), then review outputs in one batch.",
        skill_upgrade="Add a cron window that fires at night, collects results, and sends a morning digest — one review session beats constant interruptions.",
        keywords=(
            "异步", "夜间", "晚上", "下班", "凌晨", "自动", "调度", "静默", "睡着",
            "cron", "schedule", "overnight", "async", "batch", "sleep", "off hours",
        ),
    ),
    Pattern(
        key="issue-driven-learning",
        title="Issue-Driven Learning",
        summary="Convert content intake into ranked issue queues with clear execution owners.",
        skill_upgrade="Pipe interesting posts into a GitHub issue or Notion page automatically; review queue weekly and close or escalate.",
        keywords=(
            "issue", "排优先级", "任务", "github", "研究", "安排",
            "backlog", "ticket", "todo", "queue", "priorit", "task",
        ),
    ),
    Pattern(
        key="comments-and-timeline-intel",
        title="Comments + Timeline Intel",
        summary="Mine replies/comments/timeline for edge-case tactics and fast context sync.",
        skill_upgrade="Fetch reply thread alongside the main post — the real insight is often 2–3 replies deep, not in the original tweet.",
        keywords=(
            "评论区", "回复", "时间线", "监控", "抓",
            "comment", "reply", "replies", "thread", "timeline", "mentions", "latest",
        ),
    ),
    Pattern(
        key="autonomy-and-evolution",
        title="Autonomy + Evolution",
        summary="Grant bounded autonomy, let agent self-reflect, and evolve behavior over time.",
        skill_upgrade="Add a self-reflection step at end of each run: agent logs what worked, what didn't, and proposes one improvement to its own prompt.",
        keywords=(
            "进化", "soul.md", "agent.md", "无为而治", "自由", "信任", "涌现", "冥想", "活着",
            "evolv", "autonomy", "self-reflect", "soul", "persona", "identity", "trust",
        ),
    ),
    Pattern(
        key="memory-first-operations",
        title="Memory-First Operations",
        summary="Use live memory/logging to improve recall and continuity across sessions.",
        skill_upgrade="Write key decisions to a dated memory file at end of every session; add a recall check at start of next session before any action.",
        keywords=(
            "记忆", "召回", "实时",
            "memory", "log", "recall", "evolution-log", "persist", "context", "history",
        ),
    ),
    Pattern(
        key="infra-embodiment",
        title="Infra Embodiment",
        summary="Treat infra nodes (VPS/Mac/router) as body parts with resilient fallback channels.",
        skill_upgrade="Document each node's role and fallback order; add a health-check cron that alerts when a node goes dark.",
        keywords=(
            "vps", "mac", "路由器", "通道", "具身",
            "gateway", "ssh", "server", "node", "fallback", "multi-node", "infra", "bind",
        ),
    ),
    Pattern(
        key="privacy-safe-deployment",
        title="Privacy-Safe Deployment",
        summary="Design deployment workflows that avoid exposing customer secrets.",
        skill_upgrade="Audit every external call for credential leakage; store secrets in env vars only, never in prompts or logs.",
        keywords=(
            "密码", "泄露", "隐私", "密钥",
            "api key", "secret", "credential", "token", "leak", "expose", "privacy",
            "reverse proxy", "nginx", "auth",
        ),
    ),
    Pattern(
        key="build-in-public-recap",
        title="Build-in-Public Recap",
        summary="Publish concrete daily recaps with numbers, fixes, and links to reproducible steps.",
        skill_upgrade="Add a daily-recap cron: pull today's commits + metrics → draft a 3-line summary tweet with one number and one link.",
        keywords=(
            "今天", "成果", "q&a", "系列", "配图", "教程",
            "shipped", "built", "launched", "today i", "week i", "recap", "thread", "update",
        ),
    ),
    # ── Commerce / domain patterns ────────────────────────────────────────────
    Pattern(
        key="domain-flip",
        title="Domain Flip",
        summary="Register intent-clear domains at promo pricing; list immediately on Afternic/Dan at 100–300× cost.",
        skill_upgrade="Build a one-row tracker: domain | acquired | cost | list price | marketplace | listed date | sold date. Review monthly.",
        keywords=(
            "域名", "注册", "卖", "买", "出售",
            "domain", "register", "registration", "afternic", "dan.com", "sedo",
            "godaddy", "namecheap", "porkbun", "sav", "spaceship", ".app", ".io", ".ai",
            "flip", "resell",
        ),
    ),
    Pattern(
        key="revenue-milestone",
        title="Revenue Milestone",
        summary="Post revenue numbers publicly — they attract collaborators, press, and customers more than feature lists.",
        skill_upgrade="Log every paying transaction the day it happens; draft a milestone post at $100, $1k, $10k, $100k thresholds.",
        keywords=(
            "收入", "变现", "赚", "付费", "订阅",
            "revenue", "mrr", "arr", "paid", "subscriber", "profit", "$", "sale", "sold",
        ),
    ),
    Pattern(
        key="ship-fast",
        title="Ship Fast",
        summary="Launch before it feels ready — early social proof and feedback compound faster than private polish.",
        skill_upgrade="Set a 'ship it' checklist: working demo + one-line description + public URL. If all three exist, publish now.",
        keywords=(
            "发布", "上线", "推出", "开源", "上架",
            "launch", "ship", "shipped", "release", "v1", "live", "open source", "published",
            "just dropped", "introducing",
        ),
    ),
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _load_posts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    posts = payload.get("posts", []) if isinstance(payload, dict) else []
    out: list[dict[str, Any]] = []
    for row in posts:
        tweet = row.get("tweet", {}) if isinstance(row, dict) else {}
        likes   = int(tweet.get("likes")          or 0)
        views   = int(tweet.get("views")          or 0)
        retweets= int(tweet.get("retweets")       or 0)
        replies = int(tweet.get("replies_count")  or 0)
        out.append({
            "url":      row.get("url", ""),
            "text":     tweet.get("text", "") or row.get("title_rss", ""),
            "likes":    likes,
            "views":    views,
            "retweets": retweets,
            "replies":  replies,
        })
    return out


def _score(post: dict[str, Any]) -> int:
    """Influence score: views-dominant + social confirmation + engagement rate bonus."""
    likes    = int(post.get("likes",    0))
    views    = int(post.get("views",    0))
    retweets = int(post.get("retweets", 0))

    base = views + 40 * likes + 80 * retweets

    # Engagement-rate bonus: high likes/views ratio = resonated deeply
    if views > 0 and likes > 0:
        rate = likes / views * 1000   # likes per 1k views
        bonus = int(rate * views / 10)
        base += bonus

    return base


def _engagement_rate(post: dict[str, Any]) -> float | None:
    likes = int(post.get("likes", 0))
    views = int(post.get("views", 0))
    if not views or not likes:
        return None
    return round(likes / views * 1000, 2)  # per 1k views


def _detect_patterns(post: dict[str, Any]) -> list[str]:
    t = _norm(post.get("text", ""))
    return [p.key for p in PATTERNS if any(k in t for k in p.keywords)]


# ── Mining ────────────────────────────────────────────────────────────────────

def mine(posts: list[dict[str, Any]], top_k: int = 3) -> dict[str, Any]:
    mapping = {p.key: p for p in PATTERNS}
    groups: dict[str, list[dict[str, Any]]] = {p.key: [] for p in PATTERNS}
    unclassified: list[dict[str, Any]] = []

    for post in posts:
        post["score"]           = _score(post)
        post["engagement_rate"] = _engagement_rate(post)
        labels = _detect_patterns(post)
        if not labels:
            unclassified.append(post)
        else:
            for lb in labels:
                groups[lb].append(post)

    pattern_rows: list[dict[str, Any]] = []
    for key, rows in groups.items():
        if not rows:
            continue
        rows_sorted = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
        total_views = sum(int(r.get("views", 0)) for r in rows)
        avg_eng     = None
        eng_values  = [r["engagement_rate"] for r in rows if r.get("engagement_rate") is not None]
        if eng_values:
            avg_eng = round(sum(eng_values) / len(eng_values), 2)

        pattern_rows.append({
            "key":           key,
            "title":         mapping[key].title,
            "summary":       mapping[key].summary,
            "skill_upgrade": mapping[key].skill_upgrade,
            "count":         len(rows),
            "total_views":   total_views,
            "avg_views":     int(total_views / max(1, len(rows))),
            "avg_engagement_rate": avg_eng,
            "examples":      rows_sorted[:top_k],
        })

    # Sort: count first, then total signal
    pattern_rows.sort(key=lambda r: (r["count"], r["total_views"]), reverse=True)

    return {
        "post_count":         len(posts),
        "classified_count":   len(posts) - len(unclassified),
        "unclassified_count": len(unclassified),
        "patterns":           pattern_rows,
        "unclassified": sorted(
            unclassified, key=lambda r: r.get("score", 0), reverse=True
        )[:top_k],
    }


# ── Markdown renderer ─────────────────────────────────────────────────────────

def to_markdown(report: dict[str, Any], source_hint: str) -> str:
    lines: list[str] = []
    lines += [
        "# Profile Pattern Report\n",
        f"- source: {source_hint}",
        f"- posts analyzed: {report.get('post_count', 0)}",
        f"- classified: {report.get('classified_count', 0)}",
        f"- unclassified: {report.get('unclassified_count', 0)}",
        "",
    ]

    lines.append("## Dominant patterns")
    for i, p in enumerate(report.get("patterns", []), 1):
        eng = f" | avg engagement {p['avg_engagement_rate']} likes/1k views" if p.get("avg_engagement_rate") else ""
        lines.append(f"### {i}. {p['title']} ({p['count']} posts)")
        lines.append(f"**Why it matters:** {p['summary']}")
        lines.append(f"**Signal:** total_views={p['total_views']} | avg_views={p['avg_views']}{eng}")
        lines.append("**Evidence:**")
        for ex in p.get("examples", []):
            snippet = _norm(ex.get("text", ""))[:120]
            eng_r = f" | eng={ex['engagement_rate']}" if ex.get("engagement_rate") else ""
            lines.append(f"- {ex.get('url')}  (views={ex.get('views',0)}, likes={ex.get('likes',0)}, rt={ex.get('retweets',0)}{eng_r})")
            lines.append(f"  > {snippet}…")
        lines.append(f"**Skill upgrade:** {p['skill_upgrade']}")
        lines.append("")

    if report.get("unclassified"):
        lines.append("## Unclassified high-signal posts")
        lines.append("_(No pattern matched — worth inspecting manually for emerging patterns)_")
        for ex in report["unclassified"]:
            lines.append(f"- {ex.get('url')} (views={ex.get('views',0)}, likes={ex.get('likes',0)})")
        lines.append("")

    lines.append("## One immediate next step")
    patterns = report.get("patterns", [])
    if patterns:
        top = patterns[0]
        lines.append(f"The strongest pattern is **{top['title']}** ({top['count']} posts, {top['total_views']} total views).")
        lines.append(f"→ {top['skill_upgrade']}")
    else:
        lines.append("→ Fetch more posts (try 14d window) to find a dominant pattern worth acting on.")
    lines.append("")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Mine recurring patterns from X post batch JSON")
    parser.add_argument("--input",       required=True, help="Path to full posts JSON")
    parser.add_argument("--output",      default="",    help="Write markdown report here (stdout if omitted)")
    parser.add_argument("--json-output", default="",    help="Optional structured JSON output path")
    parser.add_argument("--top-k",       type=int, default=3, help="Max examples per pattern")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    posts  = _load_posts(input_path)
    report = mine(posts, top_k=max(1, args.top_k))
    md     = to_markdown(report, source_hint=str(input_path))

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
