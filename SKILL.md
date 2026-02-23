---
name: x-post-playbook
description: "Turn X/Twitter content into reusable execution playbooks. Supports (1) single-post conversion to actionable markdown and (2) profile-level pattern mining across recent posts. Use when a user asks what can be learned from a post/thread, wants SOP/task workflows extracted from X content, or asks to improve a skill using an account's recurring posting patterns."
---

# X Post Playbook

## Modes

### Mode A — Single post → playbook

Use when user gives one URL and asks "what can we learn".

### Mode B — Profile mining → pattern report

Use when user asks to learn from many posts and improve a workflow/skill.

## Mode A workflow

### 1) Fetch post

```bash
python3 /root/.openclaw/workspace/skills/x-tweet-fetcher/scripts/fetch_tweet.py \
  --url "https://x.com/user/status/123" --pretty > /tmp/post.json
```

### 2) Convert to playbook

```bash
python3 scripts/post_to_playbook.py \
  --input /tmp/post.json \
  --url "https://x.com/user/status/123" \
  --output /tmp/post-playbook.md
```

Use `--input <file.txt>` when only text is available.

### 3) Tighten output

- Keep workflow to **3–5 steps**
- Keep only executable actions
- End with exactly **one next step** (<=10 minutes)

## Mode B workflow

### 1) Collect recent post URLs

```bash
python3 /root/.openclaw/workspace/skills/x-latest-posts/scripts/fetch_x_recent_posts.py \
  --handle YuLin807 --hours 168 --max-posts 30 --json > /tmp/recent.json
```

### 2) Expand to full-text dataset

```bash
python3 scripts/build_profile_dataset.py \
  --recent-json /tmp/recent.json \
  --output /tmp/recent-full.json
```

### 3) Mine recurring patterns

```bash
python3 scripts/profile_pattern_miner.py \
  --input /tmp/recent-full.json \
  --output /tmp/pattern-report.md \
  --json-output /tmp/pattern-report.json
```

### 4) Apply improvements to skill/workflow

Prioritize patterns with highest **count + views** and convert them into:

- Automation hooks
- Guardrails
- Reusable SOP steps

## Output contract

For single post output, keep section order:

1. Source
2. Signal snapshot (if available)
3. Core thesis
4. Workflow (actionable)
5. Automation hooks
6. Referenced links
7. Next step

For profile report output, include:

1. Coverage (posts analyzed)
2. Dominant patterns + evidence links
3. Skill-upgrade suggestions (concrete)
4. One immediate next step

## References (secondary analysis artifacts)

Use these as local summaries. Prefer original source posts first.

- `references/yulin-202564-pattern.md` — single-post pattern extraction notes
- `references/yulin-7d-pattern-report.md` — multi-post pattern mining report
- `references/levelsio-2025954348933452161-pattern.md` — strategy-pattern extraction example (ownership + long horizon)
- `references/alexocheema-2016404573917683754-validation-pattern.md` — claim-validation example (plausible vs proven)

## Attribution & thanks

- Primary source ideas come from public posts by **QingYue (@YuLin807)**, especially:
  - https://x.com/YuLin807/status/2025640139947647480
  - https://x.com/YuLin807/status/2025804235707916626
  - https://x.com/YuLin807/status/2025043042840051931
  - https://x.com/YuLin807/status/2025244702992466402
- Upstream fetch dependency used by this workflow:
  - **x-tweet-fetcher** by ythx-101: https://github.com/ythx-101/x-tweet-fetcher
- This skill adds original summarization/mining scripts and does not vendor-copy x-tweet-fetcher source into this package.
- Implementation/packaging in this repo by **C3 (OpenClaw)** assisting **B3**.
- Big thanks to QingYue for openly sharing workflows and experiments in public.
