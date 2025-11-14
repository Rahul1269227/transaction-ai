#!/bin/bash
#
# Setup automatic feedback learning cron job
# This will run daily at 2 AM to learn from user feedback
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Database URL (adjust as needed)
DATABASE_URL="${DATABASE_URL:-postgresql://txn_user:txn_password@localhost:5432/transactions}"

# Cron job command
CRON_CMD="0 2 * * * cd $PROJECT_DIR && python3 scripts/feedback_learning.py --database-url \"$DATABASE_URL\" --min-feedback 10 >> logs/feedback_learning.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "feedback_learning.py"; then
    echo "❌ Feedback learning cron job already exists"
    echo "Run 'crontab -e' to edit or remove it"
    exit 1
fi

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Feedback learning cron job installed successfully!"
echo ""
echo "Schedule: Daily at 2:00 AM"
echo "Log file: $PROJECT_DIR/logs/feedback_learning.log"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove this job: crontab -e (then delete the line)"
echo ""
echo "You can also trigger learning manually via API:"
echo "  curl -X POST http://localhost:8000/api/feedback-learning"
