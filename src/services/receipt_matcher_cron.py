#!/usr/bin/env python3
"""
Receipt Matcher Cron Job

This script is designed to run as a cron job every 30 minutes to automatically
match recent purchases to store list items and update inventory.

Cron job setup:
# Run every 30 minutes
*/30 * * * * /usr/bin/python3 /path/to/receipt_matcher_cron.py >> /var/log/receipt_matcher.log 2>&1

Author: AI Agent
Date: 2025-07-11
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.services.receipt_matcher import ReceiptMatcher

# Configure logging for cron job
log_file = Path(__file__).parent / "logs" / "receipt_matcher_cron.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="🕐 %(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),  # Also log to stdout for cron
    ],
)
logger = logging.getLogger(__name__)


def run_cron_job():
    """Run the receipt matcher as a cron job"""
    logger.info("🚀 STARTING RECEIPT MATCHER CRON JOB")
    logger.info(f"📅 Execution time: {datetime.now()}")

    try:
        # Create matcher instance with 30-minute lookback
        # This ensures we catch purchases since the last run
        matcher = ReceiptMatcher(lookback_hours=1)  # 1 hour to be safe

        # Run the matching process
        stats = matcher.run_matching_process()

        # Log results for monitoring
        logger.info("📊 CRON JOB COMPLETED SUCCESSFULLY")
        logger.info(f"📈 Processing stats: {json.dumps(stats, indent=2)}")

        # Create status file for monitoring
        status_file = Path(__file__).parent / "logs" / "last_run_status.json"
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "stats": stats,
        }

        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        return 0

    except Exception as e:
        logger.error(f"💥 CRON JOB FAILED: {e}")

        # Create error status file
        status_file = Path(__file__).parent / "logs" / "last_run_status.json"
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
        }

        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        return 1


if __name__ == "__main__":
    exit(run_cron_job())
