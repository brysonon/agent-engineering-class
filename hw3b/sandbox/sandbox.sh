#!/usr/bin/env bash
# Start or stop the locked-down container the agent's shell commands run in.
# Usage: sandbox.sh up <source dir> | down
set -euo pipefail

NAME=agent-sandbox
IMAGE=agent-sandbox:latest
WORK="$HOME/agent-sandbox-workspace"

case "${1:-}" in
  up)
    docker build -q -t "$IMAGE" "$(dirname "$0")" >/dev/null
    rm -rf "$WORK" && mkdir -p "$WORK"
    # Copy code only: no .env, generated indexes, or caches.
    (cd "$2" && find . -maxdepth 1 -type f \( -name '*.py' -o -name '*.md' -o -name '*.txt' -o -name '*.json' \) \
      -exec cp {} "$WORK" \;)
    chown -R 1000:1000 "$WORK"
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker run -d --name "$NAME" \
      --network none \
      --read-only --tmpfs /tmp:size=64m \
      --cap-drop ALL --security-opt no-new-privileges \
      --pids-limit 64 --memory 512m --cpus 1 \
      -v "$WORK":/workspace \
      "$IMAGE" >/dev/null
    echo "started $NAME with $(ls "$WORK" | wc -l) files in /workspace"
    ;;
  down)
    docker rm -f "$NAME" >/dev/null && echo "removed $NAME"
    ;;
  *)
    echo "usage: $0 up <source dir> | down" >&2
    exit 1
    ;;
esac
