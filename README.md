# x-post-playbook-skill

Turn X/Twitter content into reusable execution playbooks.

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

## Attribution & thanks

- Core ideas/patterns are distilled from public posts by **QingYue (@YuLin807)**.
- Main inspiration post: https://x.com/YuLin807/status/2025640139947647480
- Additional pattern evidence from recent @YuLin807 posts is in:
  - `references/yulin-202564-pattern.md`
  - `references/yulin-7d-pattern-report.md`
- This workflow uses **x-tweet-fetcher** by ythx-101 as an upstream fetch dependency:
  - https://github.com/ythx-101/x-tweet-fetcher
- Thanks to QingYue for sharing the workflow publicly.

## Install in OpenClaw

```bash
openclaw skills install ./x-post-playbook.skill
```

Or install from this repo after cloning.
