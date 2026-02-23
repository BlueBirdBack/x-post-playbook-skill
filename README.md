# x-post-playbook-skill

Turn X/Twitter content into reusable execution playbooks.

## Built by

- **C3 🌙 (OpenClaw)** — implementation and packaging
- **B3 (BlueBirdBack)** — owner and maintainer

## What this skill does

- Convert a single X post into an actionable markdown playbook
- Mine recurring patterns from a profile's recent posts
- Generate automation hooks and one clear next action

## Beginner quick start (English prompts, no code)

You can use this skill by talking to your agent in plain English.

### 1) One post → playbook

Try:

- “Analyze this X post and turn it into an action playbook: <POST_URL>”
- “Give me core thesis, workflow steps, automation hooks, and one next step.”

Expected result: a clean markdown playbook with one practical next move.

### 2) One account (last 7 days) → pattern report

Try:

- “Learn from @<handle> recent posts in the last 7 days.”
- “Find recurring patterns and show evidence links.”
- “Suggest how to improve this skill based on top patterns.”

Expected result: dominant patterns + concrete upgrade suggestions.

### 3) Turn patterns into your own workflow

Try:

- “Turn those patterns into a simple SOP for my daily routine.”
- “Keep it ADHD-friendly: short steps, one clear next action.”

### 4) More ready-to-use prompt examples

- “Review this post and tell me if the claim is fully verified, mostly plausible, or weak: <POST_URL>”
- “Extract only practical steps from this thread. Skip opinions: <POST_URL>”
- “Compare these two posts and show where they agree/disagree: <URL_A> <URL_B>”
- “Turn this post into a 7-day execution plan with daily actions: <POST_URL>”
- “Draft a friendly X reply in Chinese based on this post: <POST_URL>”
- “Find top patterns from @<handle> this month, then give me one action I can do today.”
- “Make a decision checklist from this post (what to verify before I trust it): <POST_URL>”

### Common beginner mistakes

- Asking too broad (“analyze everything”) instead of one clear task
- Not giving a specific URL or handle
- Asking for many outputs at once instead of one focused outcome

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

Ask your OpenClaw agent to install `x-post-playbook.skill` from this repo.
(Manual command is also available if needed.)
