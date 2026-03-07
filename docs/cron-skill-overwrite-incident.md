# Incident: Cron Overwriting Manually Committed Skill Files

**Date:** 2026-03-07  
**Skill:** `x-post-playbook`  
**Script:** `cron_refresh_yulin_skill.sh`  
**Reported by:** Max (OpenClaw agent)  
**Resolved by:** Max — commit `08ad24d`

---

## What Happened

A cron script that periodically refreshed YuLin pattern data was also overwriting `scripts/` and `SKILL.md` in the public GitHub repo. When Max pushed skill improvements, the next cron run stomped them silently.

**Broken flow:**
```
pull repo → mine patterns → rsync SKILL_SRC/* → PUB_REPO (overwrites everything)
```

The cron was pushing its entire local skill source directory back to GitHub, including scripts and SKILL.md — files it had no business touching.

---

## Root Cause

The cron script managed two concerns in one:
1. **Data refresh** — fetching fresh pattern data from X, mining it, updating `references/`
2. **Code sync** — rsyncing scripts and SKILL.md between local and repo

It treated the local `SKILL_SRC` as the source of truth and pushed it back to the repo wholesale. Any manual changes made directly to GitHub (PRs, commits) were invisible to it and got clobbered on the next run.

---

## The Fix

**After (fixed):**
```
pull repo → sync repo scripts/SKILL.md → SKILL_SRC → mine patterns → rsync only references/ → push
```

Key changes:
- **Pull first, always** — sync FROM the repo (not from local) before doing anything
- **Cron only owns `references/` and `.skill` bundle** — never touches `scripts/` or `SKILL.md`
- Scripts and SKILL.md are managed by git (humans + agents via PRs/commits), not by cron

The cron self-healed on its next run by pulling the fixed script from GitHub.

---

## Lesson for Cron Scripts That Touch Shared Repos

If you write a cron that commits/pushes to a shared GitHub repo:

1. **Divide ownership clearly.** Decide which files the cron "owns" and never let it touch files owned by humans or other agents.
2. **Always `git pull --rebase` before pushing.** Never push on a stale local state.
3. **Use narrow `git add <specific-paths>`** — never `git add .` or `git add -A`. Explicitly list what the cron is allowed to stage.
4. **Sync FROM repo TO local before mining/processing** — local state may be stale; the repo is the source of truth.
5. **Test with `--dry-run` or `git diff --stat` before committing** — log what would change so you can audit runs.

---

## Detection

If you suspect a cron is stomping changes:

```bash
# Check recent commit authors/messages in the repo
gh api repos/OWNER/REPO/commits --jq '.[].commit | [.author.date, .message[:60]] | @tsv' | head -20

# Look for "chore: refresh" or bot-style commit messages
# Cross-reference timestamps with your cron schedule
```

---

## Status

✅ Resolved. Cron now only writes to `references/` and `.skill` bundle. Manual commits to `scripts/` and `SKILL.md` are safe.
