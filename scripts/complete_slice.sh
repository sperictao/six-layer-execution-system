#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
WORKSPACE="${SIX_LAYER_WORKSPACE:-${SCRIPT_DIR:h}}"
CHECKER="$WORKSPACE/scripts/check_active_consistency.py"
CHECK_SUITE="$WORKSPACE/scripts/run_execution_system_checks.py"
CLOSEOUT_READY="$WORKSPACE/scripts/check_closeout_ready.py"
CREATE="$WORKSPACE/scripts/create_slice_closeout.py"
QUEUE="$WORKSPACE/scripts/queue_slice_notification.py"
FLUSH="$WORKSPACE/scripts/flush_slice_notifications.py"
ACK="$WORKSPACE/scripts/ack_slice_notification.py"
REQUEUE="$WORKSPACE/scripts/requeue_inflight_notifications.py"
PAYLOAD="$WORKSPACE/scripts/send_slice_notification_payload.py"
LAST_CLOSEOUT="$WORKSPACE/memory/last-slice-closeout.json"
LAST_NOTIFICATION="$WORKSPACE/memory/last-slice-notification.json"
LEDGER="$WORKSPACE/scripts/active_ledger.py"

usage() {
  cat <<'EOF'
usage:
  complete_slice.sh prepare
  complete_slice.sh payload
  complete_slice.sh ack <dedupe_key>
  complete_slice.sh fail

modes:
  prepare  run the execution-system check suite plus closeout-ready gate, create completed-slice artifact from the current focus roadmap activity, enqueue it, flush one item to inflight, and persist the notification payload
  payload  print the canonical Feishu-ready payload from the completed-slice artifact
  ack      mark an inflight notification as sent after a successful delivery and clear cached payload files
  fail     move inflight notifications back to pending after a failed delivery attempt and clear cached notification payload
EOF
}

focus_scalar() {
  local field="$1"
  python3 - "$LEDGER" "$field" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
from active_ledger import parse_ledger
field = sys.argv[2]
ledger = parse_ledger()
activity = ledger.get_current_focus_activity()
if activity is None:
    raise SystemExit(1)
value = activity.scalar(field)
if value is None:
    raise SystemExit(1)
print(value)
PY
}

focus_validations() {
  python3 - "$LEDGER" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
from active_ledger import parse_ledger
ledger = parse_ledger()
activity = ledger.get_current_focus_activity()
if activity is None:
    raise SystemExit(1)
print(json.dumps(activity.items("last_validation"), ensure_ascii=False))
PY
}

clear_notification_cache() {
  cat > "$LAST_NOTIFICATION" <<'EOF'
{}
EOF
}

clear_closeout_cache() {
  cat > "$LAST_CLOSEOUT" <<'EOF'
{}
EOF
}

mode="${1:-prepare}"

case "$mode" in
  prepare)
    if [[ $# -ne 1 ]]; then
      usage >&2
      exit 2
    fi
    python3 "$CHECK_SUITE"
    python3 "$CLOSEOUT_READY"
    activity_id="$(focus_scalar activity_id)"
    current_focus_activity_id="$activity_id"
    activity_type="$(focus_scalar type)"
    if [[ "$activity_type" != "roadmap" ]]; then
      echo "FOCUS_ACTIVITY_NOT_ROADMAP:$activity_id:$activity_type" >&2
      exit 1
    fi
    repo="$(focus_scalar repo)"
    completed_slice_id="$(focus_scalar current_slice_id)"
    next_slice_id="$(focus_scalar next_slice_id)"
    commit="$(focus_scalar last_commit)"
    validations_json="$(focus_validations)"
    cmd=(python3 "$CREATE" --activity-id "$activity_id" --current-focus-activity-id "$current_focus_activity_id" --activity-type "$activity_type" --repo "$repo" --completed-slice-id "$completed_slice_id" --next-slice-id "$next_slice_id" --commit "$commit")
    while IFS= read -r validation; do
      [[ -n "$validation" ]] && cmd+=(--validation "$validation")
    done < <(python3 - <<'PY' "$validations_json"
import json, sys
for item in json.loads(sys.argv[1]):
    print(item)
PY
)
    artifact="$(${cmd[@]})"
    python3 "$QUEUE" >/dev/null
    flushed="$(python3 "$FLUSH")"
    if [[ "$flushed" == "NO_PENDING_NOTIFICATIONS" ]]; then
      clear_notification_cache
      echo "NO_PENDING_NOTIFICATIONS"
      exit 0
    fi
    printf '%s\n' "$flushed" > "$LAST_NOTIFICATION"
    printf '%s\n' "$flushed"
    ;;
  payload)
    if [[ $# -ne 1 ]]; then
      usage >&2
      exit 2
    fi
    python3 "$PAYLOAD"
    ;;
  ack)
    if [[ $# -ne 2 ]]; then
      usage >&2
      exit 2
    fi
    COMPLETE_SLICE_ACK=1 python3 "$ACK" "$2"
    clear_notification_cache
    clear_closeout_cache
    ;;
  fail)
    if [[ $# -ne 1 ]]; then
      usage >&2
      exit 2
    fi
    python3 "$REQUEUE"
    clear_notification_cache
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
