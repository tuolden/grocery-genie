#!/usr/bin/env python3
"""
Receipt Matcher HTTP API

Simple HTTP endpoint for triggering receipt matching on-demand.
Can be called via curl or integrated into other systems.

Usage:
    python receipt_matcher_api.py

Endpoints:
    GET  /health - Health check
    POST /match  - Trigger receipt matching
    GET  /status - Get last run status

Author: AI Agent
Date: 2025-07-11
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from receipt_matcher import ReceiptMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="🌐 %(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReceiptMatcherHandler(BaseHTTPRequestHandler):
    """HTTP request handler for receipt matcher API"""

    def log_message(self, msg_format, *args):
        """Override to use our logger"""
        logger.info(f"HTTP {msg_format % args}")

    def do_GET(self):  # noqa: N802
        """Handle GET requests"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/health":
            self._handle_health()
        elif parsed_path.path == "/status":
            self._handle_status()
        else:
            self._send_error(404, "Not Found")

    def do_POST(self):  # noqa: N802
        """Handle POST requests"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/match":
            self._handle_match()
        else:
            self._send_error(404, "Not Found")

    def _handle_health(self):
        """Health check endpoint"""
        response = {
            "status": "healthy",
            "service": "receipt-matcher-api",
            "timestamp": datetime.now().isoformat(),
        }
        self._send_json_response(200, response)

    def _handle_status(self):
        """Get last run status"""
        try:
            status_file = Path(__file__).parent / "logs" / "last_run_status.json"

            if status_file.exists():
                with open(status_file) as f:
                    status_data = json.load(f)
                self._send_json_response(200, status_data)
            else:
                response = {
                    "status": "no_previous_runs",
                    "message": "No previous runs found",
                }
                self._send_json_response(200, response)

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self._send_error(500, f"Error getting status: {e}")

    def _handle_match(self):
        """Trigger receipt matching"""
        try:
            # Parse request body for parameters
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    params = json.loads(post_data.decode("utf-8"))
                except json.JSONDecodeError:
                    params = {}
            else:
                params = {}

            # Get parameters
            lookback_hours = params.get("lookback_hours", 24)

            logger.info(
                f"🚀 Triggering receipt matching (lookback: {lookback_hours} hours)"
            )

            # Run matching in a separate thread to avoid blocking
            def run_matching():
                try:
                    matcher = ReceiptMatcher(lookback_hours=lookback_hours)
                    stats = matcher.run_matching_process()

                    # Save status
                    status_file = (
                        Path(__file__).parent / "logs" / "last_run_status.json"
                    )
                    status_file.parent.mkdir(exist_ok=True)

                    status_data = {
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "trigger": "api",
                        "stats": stats,
                    }

                    with open(status_file, "w") as f:
                        json.dump(status_data, f, indent=2)

                    logger.info("✅ API-triggered matching completed successfully")

                except Exception as e:
                    logger.error(f"❌ API-triggered matching failed: {e}")

                    # Save error status
                    status_file = (
                        Path(__file__).parent / "logs" / "last_run_status.json"
                    )
                    status_file.parent.mkdir(exist_ok=True)

                    status_data = {
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "trigger": "api",
                        "error": str(e),
                    }

                    with open(status_file, "w") as f:
                        json.dump(status_data, f, indent=2)

            # Start matching in background
            thread = threading.Thread(target=run_matching)
            thread.daemon = True
            thread.start()

            # Return immediate response
            response = {
                "status": "started",
                "message": "Receipt matching started in background",
                "timestamp": datetime.now().isoformat(),
                "parameters": {
                    "lookback_hours": lookback_hours,
                },
            }
            self._send_json_response(202, response)

        except Exception as e:
            logger.error(f"Error handling match request: {e}")
            self._send_error(500, f"Error starting match: {e}")

    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        response_json = json.dumps(data, indent=2)

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_json)))
        self.end_headers()
        self.wfile.write(response_json.encode("utf-8"))

    def _send_error(self, status_code, message):
        """Send error response"""
        error_response = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
        }
        self._send_json_response(status_code, error_response)


def run_api_server(port=8080):
    """Run the HTTP API server"""
    logger.info(f"🌐 Starting Receipt Matcher API server on port {port}")

    server_address = ("", port)
    httpd = HTTPServer(server_address, ReceiptMatcherHandler)

    logger.info(f"🚀 Server running at http://localhost:{port}")
    logger.info("📋 Available endpoints:")
    logger.info("   GET  /health - Health check")
    logger.info("   POST /match  - Trigger receipt matching")
    logger.info("   GET  /status - Get last run status")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Receipt Matcher HTTP API")
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the server on (default: 8080)",
    )

    args = parser.parse_args()

    run_api_server(args.port)
