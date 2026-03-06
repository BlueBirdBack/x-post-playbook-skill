# x-post-playbook-skill

Turn X/Twitter content into reusable execution playbooks.

## Built by

- **Ash 🌿 (OpenClaw)** — architecture, content-type engine, engagement analysis, agent-browser integration
- **C3 🌙 (OpenClaw)** — initial implementation and packaging
- **B3 (BlueBirdBack)** — owner and maintainer

## What this skill does

- **Mode A** — Fetch any X post and convert it into a structured playbook: thesis, engagement quality, key numbers, why it worked, content-type-aware workflow steps, and one actionable next step
- **Mode B** — Mine an account's recent posts for dominant patterns (async ops, domain flipping, ship-fast, memory-first, etc.) with per-pattern engagement rates and concrete upgrade suggestions
- **Mode C** — Explain why a specific post performed well (virality drivers, engagement rate, reply dynamics)

### Content types detected automatically

| Type | Example signal | Workflow template |
|------|---------------|-------------------|
| `commerce` | "$4.99", "domain", "sold" | 5-step domain/asset flip playbook |
| `announcement` | "launched", "shipped", "上线" | test → compare → share |
| `question` | ends with `?`, "why/how/what" | hypothesis → experiment → publish |
| `workflow` | "step", "cron", "agent", "自动" | capture → extract → automate → review |
| `opinion` | default | claim → test → verdict |

## Beginner quick start (English prompts, no code)

Talk to your agent in plain English — no commands needed.

### Mode A — One post → playbook

- `"What can we learn from this post? <POST_URL>"`
- `"Turn this into an action playbook: <POST_URL>"`
- `"Give me the core thesis, workflow steps, automation hooks, and one next step for: <POST_URL>"`

Expected output: a structured markdown playbook with engagement quality score, key numbers extracted, and a content-type-aware 5-step workflow.

### Mode B — One account → pattern report

- `"Learn from @<handle>'s recent posts in the last 7 days."`
- `"Find recurring patterns from @<handle> and suggest what to add to my workflow."`
- `"Mine @<handle> for top patterns this week, then give me one action I can do today."`

Expected output: dominant patterns ranked by engagement rate, evidence links, and a concrete per-pattern skill upgrade.

### Mode C — Why did this post work?

- `"Why did this post get <N> views and <M> likes? <POST_URL>"`
- `"Explain the virality drivers for: <POST_URL>"`
- `"What made this perform so well? <POST_URL>"`

Expected output: engagement rate label (🔥 viral / ⚡ strong / 👍 normal / 📉 low), reply dynamics, format analysis, and a one-paragraph explanation.

### More ready-to-use prompts

- `"Is this claim verified, mostly plausible, or weak? <POST_URL>"`
- `"Extract only practical steps. Skip opinions: <POST_URL>"`
- `"Compare these two posts — where do they agree and disagree? <URL_A> <URL_B>"`
- `"Turn this into a 7-day execution plan with daily actions: <POST_URL>"`
- `"Draft a friendly X reply in Chinese for: <POST_URL>"`
- `"Make a decision checklist from this post: <POST_URL>"`

### Common mistakes

- Asking too broad ("analyze everything") instead of one clear task
- Not providing a specific URL or handle
- Asking for many outputs at once instead of one focused result

## Install in OpenClaw

```bash
# Ask your agent:
"Install the x-post-playbook skill from https://github.com/BlueBirdBack/x-post-playbook-skill"
```

Or clone manually:

```bash
git clone https://github.com/BlueBirdBack/x-post-playbook-skill \
  ~/.openclaw/workspace/skills/x-post-playbook
npm install -g agent-browser && agent-browser install --with-deps
```

## Attribution & thanks

- Primary source ideas from public posts by **QingYue (@YuLin807)**:
  - https://x.com/YuLin807/status/2025640139947647480
  - https://x.com/YuLin807/status/2025804235707916626
  - https://x.com/YuLin807/status/2025043042840051931
  - https://x.com/YuLin807/status/2025244702992466402
- Fetch dependencies:
  - **agent-browser** by Vercel Labs (primary): https://github.com/vercel-labs/agent-browser
  - **x-tweet-fetcher** by ythx-101 (fallback): https://github.com/ythx-101/x-tweet-fetcher
- Reference analysis artifacts in `references/`
- Huge thanks to QingYue for sharing workflows openly.
