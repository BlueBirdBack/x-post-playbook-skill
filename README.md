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
