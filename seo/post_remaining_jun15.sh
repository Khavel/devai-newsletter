#!/usr/bin/env bash
set -e
SCHEDULER="python C:/Users/ceja_/Desktop/Desarrollos/Spam/lib/x_scheduler.py"
SEO="C:/Users/ceja_/Desktop/Desarrollos/devai-newsletter/seo"
SPAM="C:/Users/ceja_/Desktop/Desarrollos/Spam"

check_can_post() {
  $SCHEDULER check "$1" 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); exit(0 if d['can_post_now'] else 1)"
}

# --- FutProbLab ---
echo "Waiting for FutProbLab scheduler..."
until check_can_post FutProbLab; do sleep 30; done
echo "FutProbLab clear — posting..."
cd "$SEO"
FPL_RESULT=$(python twitter_api_post.py --account FutProbLab --file tweet_fpl_jun15.txt 2>&1)
echo "$FPL_RESULT"
FPL_URL=$(echo "$FPL_RESULT" | grep -oP 'https://x\.com/\S+')

# --- DevAISemanal ---
echo "Waiting for DevAISemanal scheduler..."
until check_can_post DevAISemanal; do sleep 30; done
echo "DevAISemanal clear — posting..."
DEVAI_RESULT=$(python twitter_api_post.py --account DevAISemanal --file tweet_devai_jun15.txt 2>&1)
echo "$DEVAI_RESULT"
DEVAI_URL=$(echo "$DEVAI_RESULT" | grep -oP 'https://x\.com/\S+')

# --- Record run ---
echo "Recording run..."
cd "$SPAM"
python lib/record_run.py \
  --routine twitter-daily-posts \
  --category twitter \
  --status ok \
  --summary "Posted 3 tweets (@StatLineNerd educational, @FutProbLab WC Day5 Spain, @DevAISemanal specialized agents)" \
  --metric tweets=3 \
  --link "@StatLineNerd|https://x.com/StatLineNerd/status/2066508979560124878" \
  --link "@FutProbLab|$FPL_URL" \
  --link "@DevAISemanal|$DEVAI_URL" \
  2>&1

echo "ALL DONE"
