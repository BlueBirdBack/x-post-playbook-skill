#!/usr/bin/env bash
set -euo pipefail

WS="/root/.openclaw/workspace"
SKILL_SRC="$WS/skills/x-post-playbook"
PUB_REPO="$WS/x-post-playbook-skill"
TMP_DIR="$WS/downloads/x-post-playbook-cron"

RECENT_JSON="$TMP_DIR/YuLin807-recent-168h.json"
FULL_JSON="$TMP_DIR/YuLin807-recent-168h-full.json"
NEW_REPORT_MD="$TMP_DIR/yulin-7d-pattern-report.new.md"
NEW_REPORT_JSON="$TMP_DIR/yulin-7d-pattern-report.new.json"

REPORT_TARGET="$SKILL_SRC/references/yulin-7d-pattern-report.md"
FINGERPRINT_TARGET="$SKILL_SRC/references/yulin-pattern-fingerprint.json"
FINGERPRINT_NEW="$TMP_DIR/yulin-pattern-fingerprint.new.json"

log() {
  echo "[x-post-playbook-cron] $*"
}

mkdir -p "$TMP_DIR"

log "Pulling latest public repo"
git -C "$PUB_REPO" pull --rebase --autostash >/dev/null

log "Fetching recent posts (last 7 days)"
python3 "$WS/skills/x-latest-posts/scripts/fetch_x_recent_posts.py" \
  --handle YuLin807 --hours 168 --max-posts 30 --json > "$RECENT_JSON"

log "Expanding URL list into full dataset"
python3 "$SKILL_SRC/scripts/build_profile_dataset.py" \
  --recent-json "$RECENT_JSON" \
  --output "$FULL_JSON" \
  --sleep-ms 100 >/dev/null

log "Mining recurring patterns"
python3 "$SKILL_SRC/scripts/profile_pattern_miner.py" \
  --input "$FULL_JSON" \
  --output "$NEW_REPORT_MD" \
  --json-output "$NEW_REPORT_JSON" \
  --top-k 3 >/dev/null

log "Building lightweight fingerprint (key+count only)"
python3 - "$NEW_REPORT_JSON" > "$FINGERPRINT_NEW" <<'PY'
import json
import sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
fp = [{"key": x.get("key"), "count": x.get("count")} for x in p.get("patterns", [])]
print(json.dumps({"patterns": fp}, ensure_ascii=False, indent=2))
PY

if [[ -f "$FINGERPRINT_TARGET" ]] && cmp -s "$FINGERPRINT_TARGET" "$FINGERPRINT_NEW"; then
  log "No structural pattern change (key/count unchanged). Skipping skill update."
  exit 0
fi

log "Pattern structure changed. Updating skill references."
cp "$NEW_REPORT_MD" "$REPORT_TARGET"
cp "$FINGERPRINT_NEW" "$FINGERPRINT_TARGET"

log "Repackaging skill"
python3 /usr/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py \
  "$SKILL_SRC" "$WS/skills/dist" >/dev/null

log "Syncing skill files into public repo"
cp "$SKILL_SRC/SKILL.md" "$PUB_REPO/SKILL.md"
rsync -a --delete "$SKILL_SRC/scripts/" "$PUB_REPO/scripts/"
rsync -a --delete "$SKILL_SRC/references/" "$PUB_REPO/references/"
cp "$WS/skills/dist/x-post-playbook.skill" "$PUB_REPO/x-post-playbook.skill"

cd "$PUB_REPO"

if git diff --quiet && git diff --cached --quiet; then
  log "No git changes after sync."
  exit 0
fi

git add SKILL.md scripts references x-post-playbook.skill

if git diff --cached --quiet; then
  log "Nothing staged after add."
  exit 0
fi

STAMP="$(date -u +%Y-%m-%d)"
git commit -m "chore: refresh YuLin pattern report (${STAMP})" >/dev/null
git push >/dev/null

log "Done. Skill updated and pushed."
