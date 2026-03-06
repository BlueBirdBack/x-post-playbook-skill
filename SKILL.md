---
name: x-post-playbook
description: "Turn X/Twitter content into reusable execution playbooks. Supports (1) single-post conversion to actionable markdown, (2) profile-level pattern mining across recent posts, and (3) engagement analysis explaining why a post performed well. Use when a user asks what can be learned from a post/thread, wants SOP/task workflows extracted from X content, or asks to improve a skill using an account's recurring posting patterns."
---

# X Post Playbook

## Modes

| Mode | Trigger phrase | Output |
|------|---------------|--------|
| **A** — Single post → playbook | "what can we learn from \<url\>" | Markdown playbook: thesis, workflow, hooks, next step |
| **B** — Profile mining | "learn from @handle recent posts" | Pattern report: dominant themes, evidence links, skill upgrades |
| **C** — Engagement analysis | "why did this post work" | Explains virality drivers for a single post |

---

## Mode A — Single post → playbook

### 1) Fetch post

**Primary — agent-browser** (no X account required):

```bash
bash scripts/fetch_tweet.sh "https://x.com/user/status/123" /tmp/post.json
```

Requirements: `npm install -g agent-browser && agent-browser install --with-deps`

**Fallback — x-tweet-fetcher** (if agent-browser unavailable):

```bash
python3 /root/.openclaw/workspace/skills/x-tweet-fetcher/scripts/fetch_tweet.py \
  --url "https://x.com/user/status/123" --pretty > /tmp/post.json
```

**Text-only fallback** (paste tweet text directly):

```bash
echo "paste tweet text here" > /tmp/post.txt
```

### 2) Convert to playbook

```bash
python3 scripts/post_to_playbook.py \
  --input /tmp/post.json \
  --url "https://x.com/user/status/123" \
  --output /tmp/post-playbook.md

cat /tmp/post-playbook.md
```

Use `--input /tmp/post.txt` when only text is available.

### 3) Tighten output

- Keep workflow to **3–5 steps maximum**
- Steps should be content-type-aware (commerce ≠ workflow ≠ opinion)
- End with exactly **one next step** the user can execute in ≤ 10 minutes

---

## Mode B — Profile mining → pattern report

### 1) Collect recent post URLs

```bash
python3 /root/.openclaw/workspace/skills/x-latest-posts/scripts/fetch_x_recent_posts.py \
  --handle <HANDLE> --hours 168 --max-posts 30 --json > /tmp/recent.json
```

Replace `<HANDLE>` with any public X account handle (no @).

### 2) Expand to full-text dataset

```bash
python3 scripts/build_profile_dataset.py \
  --recent-json /tmp/recent.json \
  --output /tmp/recent-full.json
```

Uses agent-browser automatically if x-tweet-fetcher is unavailable.

### 3) Mine recurring patterns

```bash
python3 scripts/profile_pattern_miner.py \
  --input /tmp/recent-full.json \
  --output /tmp/pattern-report.md \
  --json-output /tmp/pattern-report.json \
  --top-k 3
```

### 4) Apply improvements

Prioritize patterns with highest **count × avg_engagement_rate** — those are the ones the audience actually responded to, not just saw.

Convert top pattern's `skill_upgrade` field into a concrete cron/automation/habit.

---

## Mode C — Engagement analysis

Run Mode A first, then ask:

> "Why did this post get \<N\> views and \<M\> likes?"

The playbook already includes a **"Why it worked"** section. If more depth is needed:

1. Note: content type (commerce / workflow / announcement / question / opinion)
2. Check: engagement rate = likes / views × 1000. Above 5 = strong. Above 20 = viral.
3. Check: reply:like ratio. Above 0.5 = controversy. Below 0.05 = pure appreciation.
4. Check: post length. Short (< 140 chars) + one number = highest shareability.
5. Check: does it make one surprising, verifiable claim?

---

## Output contract

### Single post playbook (Mode A/C)

Section order:

1. Source (url + detected content type)
2. Signal snapshot (likes, views, author, engagement quality label)
3. Key numbers (prices, durations, multipliers extracted from text)
4. Core thesis (one sentence)
5. Why it worked (engagement drivers)
6. Workflow (3–5 actionable steps, content-type-aware)
7. Automation hooks (concrete next actions for your stack)
8. Referenced links
9. Next step (one action, ≤ 10 minutes)

### Profile report (Mode B)

Section order:

1. Coverage (posts analyzed, classified, unclassified)
2. Dominant patterns with evidence links + avg engagement rate
3. Per-pattern skill upgrade (concrete, one sentence)
4. One immediate next step (top pattern's upgrade action)

---

## Content types detected automatically

| Type | Signals | Workflow template |
|------|---------|-------------------|
| `commerce` | price/cost/domain/sell/flip | 5-step domain/asset flip playbook |
| `announcement` | launch/ship/release/上线 | test → compare → share |
| `question` | ends with ? / why/how/what | hypothesis → experiment → publish |
| `workflow` | step/process/cron/agent/自动 | capture → extract → automate → review |
| `opinion` | default | claim → test → verdict |

---

## References (secondary analysis artifacts)

- `references/yulin-7d-pattern-report.md` — multi-post pattern mining report
- `references/levelsio-2025954348933452161-pattern.md` — ownership + long-horizon strategy extraction
- `references/levelsio-2025962414085210559-speed-vs-safety-pattern.md` — speed-vs-safety extraction
- `references/steipete-2020704611640705485-persona-patch-pattern.md` — persona-patch / voice-tuning extraction
- `references/alexocheema-2016404573917683754-validation-pattern.md` — claim-validation (plausible vs proven)

---

## Attribution & thanks

- Primary source ideas from public posts by **QingYue (@YuLin807)**:
  - https://x.com/YuLin807/status/2025640139947647480
  - https://x.com/YuLin807/status/2025804235707916626
  - https://x.com/YuLin807/status/2025043042840051931
  - https://x.com/YuLin807/status/2025244702992466402
- Fetch dependencies:
  - **agent-browser** by Vercel Labs (primary): https://github.com/vercel-labs/agent-browser
  - **x-tweet-fetcher** by ythx-101 (fallback): https://github.com/ythx-101/x-tweet-fetcher
- This skill adds original summarization/mining scripts and does not vendor-copy either fetch dependency.
- Implementation/packaging by **C3 (OpenClaw)** assisting **B3 (BlueBirdBack)**.
- Big thanks to QingYue for sharing workflows openly.
