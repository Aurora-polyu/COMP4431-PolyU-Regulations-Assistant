"""Minimal app that renders the feedback hook for a fixed message (tests only)."""

import json
import os

from src.ui.feedback import render_rating_and_report

message = json.loads(os.environ["HOOK_MSG"])
render_rating_and_report(message)
