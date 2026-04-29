#!/bin/bash
# summarizvid — one-command installer
# Usage: bash install.sh

set -euo pipefail

REPO_URL="https://github.com/rustamnova/summarizvid"
BOT_NAME="summarizvid"
WORKDIR="${BOTS_DIR:-/root/.bots}"
BOT_DIR="$WORKDIR/$BOT_NAME"

echo "============================================"
echo "  summarizvid installer"
echo "============================================"

# === Step 1: .env ===
echo ""
echo "📋 Paste your .env content (copy from .env.example and fill in), then press Ctrl+D:"
ENV_TEMP=$(mktemp)
cat > "$ENV_TEMP"

source "$ENV_TEMP" 2>/dev/null || true
if [[ -z "${BOT_TOKEN:-}" ]]; then
  echo "❌ BOT_TOKEN is required in .env"
  rm -f "$ENV_TEMP"
  exit 1
fi
if [[ -z "${XAI_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "❌ At least one of XAI_API_KEY or OPENAI_API_KEY is required"
  rm -f "$ENV_TEMP"
  exit 1
fi

# === Step 2: Clone ===
mkdir -p "$WORKDIR"
echo ""
echo "📥 Cloning $REPO_URL → $BOT_DIR"
rm -rf "$BOT_DIR"
git clone "$REPO_URL.git" "$BOT_DIR"

mkdir -p "$BOT_DIR/logs"
INSTALL_LOG="$BOT_DIR/logs/install.txt"
exec > >(tee -a "$INSTALL_LOG") 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Installing $BOT_NAME..."

cp "$ENV_TEMP" "$BOT_DIR/.env"
rm -f "$ENV_TEMP"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ .env written"

# === Step 3: System packages ===
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📦 Installing system packages..."
apt-get update -qq
apt-get install -y python3 python3-venv python3-dev git screen ffmpeg build-essential
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ System packages installed"

# === Step 4: Python venv ===
cd "$BOT_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🐍 Setting up Python venv..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Python venv ready"

# === Step 5: Scripts ===
cat > start.sh << 'STARTEOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
mkdir -p logs
python summarizvid.py
STARTEOF

cat > stop.sh << 'STOPEOF'
#!/bin/bash
cd "$(dirname "$0")"
SESSION="summarizvid"
if screen -list | grep -q "\.$SESSION"; then
  screen -S "$SESSION" -X quit && echo "✅ Stopped"
else
  echo "⚠️  Screen session not found"
fi
STOPEOF

cat > restart.sh << 'RESTARTEOF'
#!/bin/bash
cd "$(dirname "$0")"
SESSION="summarizvid"
screen -S "$SESSION" -X quit 2>/dev/null || true
sleep 1
screen -dmS "$SESSION" ./start.sh
echo "✅ Restarted in screen: $SESSION"
RESTARTEOF

chmod +x start.sh stop.sh restart.sh

# === Step 6: Launch ===
screen -S summarizvid -X quit 2>/dev/null || true
screen -dmS summarizvid "$BOT_DIR/start.sh"

sleep 2
if screen -list | grep -q "\.summarizvid"; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Bot launched in screen session 'summarizvid'"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Launch failed — check logs/errors.txt"
fi

echo ""
echo "============================================"
echo "  Installation complete!"
echo "  Attach: screen -r summarizvid"
echo "  Logs:   $BOT_DIR/logs/"
echo "============================================"
