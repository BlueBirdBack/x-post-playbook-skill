# x-post-playbook-skill

Turn X/Twitter content into reusable execution playbooks.

## Built by

- **C3 🌙 (OpenClaw)** — implementation and packaging
- **B3 (BlueBirdBack)** — owner and maintainer

## What this skill does

- Convert a single X post into an actionable markdown playbook
- Mine recurring patterns from a profile's recent posts
- Generate automation hooks and one clear next action

## Included files

- `SKILL.md`
- `scripts/post_to_playbook.py`
- `scripts/build_profile_dataset.py`
- `scripts/profile_pattern_miner.py`
- `references/yulin-202564-pattern.md`
- `references/yulin-7d-pattern-report.md`
- `x-post-playbook.skill` (packaged skill file)

## Beginner quick start (copy-paste)

> No coding needed. Just run the commands.

### 1) One post → playbook

```bash
cd /root/.openclaw/workspace/x-post-playbook-skill

python3 /root/.openclaw/workspace/skills/x-tweet-fetcher/scripts/fetch_tweet.py \
  --url "https://x.com/YuLin807/status/2025640139947647480" \
  --pretty > /tmp/post.json

python3 scripts/post_to_playbook.py \
  --input /tmp/post.json \
  --url "https://x.com/YuLin807/status/2025640139947647480" \
  --output /tmp/post-playbook.md

sed -n '1,120p' /tmp/post-playbook.md
```

Expected: a clean markdown playbook with workflow + automation hooks + one next step.

### 2) Profile (7 days) → pattern report

```bash
cd /root/.openclaw/workspace/x-post-playbook-skill

python3 /root/.openclaw/workspace/skills/x-latest-posts/scripts/fetch_x_recent_posts.py \
  --handle YuLin807 --hours 168 --max-posts 20 --json > /tmp/recent.json

python3 scripts/build_profile_dataset.py \
  --recent-json /tmp/recent.json \
  --output /tmp/recent-full.json

python3 scripts/profile_pattern_miner.py \
  --input /tmp/recent-full.json \
  --output /tmp/pattern-report.md \
  --json-output /tmp/pattern-report.json

sed -n '1,180p' /tmp/pattern-report.md
```

Expected: dominant patterns, evidence links, and concrete skill-upgrade suggestions.

### 3) Use your own account

```bash
HANDLE="your_handle"   # with or without @

python3 /root/.openclaw/workspace/skills/x-latest-posts/scripts/fetch_x_recent_posts.py \
  --handle "$HANDLE" --hours 168 --max-posts 20 --json > /tmp/recent.json
```

Then run the last two commands from section 2 (dataset + pattern report).

### Common beginner mistakes

- Forgetting to `cd` into this repo before running `scripts/...`
- Running profile mode without `x-latest-posts` and `x-tweet-fetcher` available
- Using output paths you cannot write to

## Attribution & thanks

- Primary source ideas come from original public posts by **QingYue (@YuLin807)**:
  - https://x.com/YuLin807/status/2025640139947647480
  - https://x.com/YuLin807/status/2025804235707916626
  - https://x.com/YuLin807/status/2025043042840051931
  - https://x.com/YuLin807/status/2025244702992466402
- The local reference files are secondary analysis artifacts derived from those posts:
  - `references/yulin-202564-pattern.md`
  - `references/yulin-7d-pattern-report.md`
- Upstream fetch dependency:
  - **x-tweet-fetcher** by ythx-101: https://github.com/ythx-101/x-tweet-fetcher
- Implementation/packaging in this repo by **C3 (OpenClaw)** assisting **B3**.
- Huge thanks to QingYue for sharing workflows openly.

## Install in OpenClaw

```bash
openclaw skills install ./x-post-playbook.skill
```

Or install from this repo after cloning.
