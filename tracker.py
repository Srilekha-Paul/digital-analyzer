"""
Digital Detox Tracker — tracker.py
Business logic: usage data, productivity scoring,
AI-style suggestions, and CSV report generation.
"""

import json
import os
import random
import csv
import io
from datetime import datetime

from db import get_today_usage

# Path to the usage.json seed file (optional external data source)
USAGE_JSON = os.path.join(os.path.dirname(__file__), 'usage.json')


# ── Usage Data ────────────────────────────────────────────────────

def get_usage_data(user_id: int) -> dict:
    """
    Returns usage data for the current user.
    Prefers DB records; falls back to usage.json for demo purposes.
    """
    rows = get_today_usage(user_id)

    if not rows:
        # Load from usage.json as demo / seed data
        rows = _load_json_usage()

    apps        = [{'name': r['app_name'], 'minutes': round(r['minutes'], 1)} for r in rows]
    total_mins  = sum(a['minutes'] for a in apps)
    pickups     = _estimate_pickups(total_mins)

    return {
        'apps':          apps,
        'total_minutes': round(total_mins, 1),
        'pickups':       pickups,
        'date':          datetime.now().strftime('%Y-%m-%d')
    }


def _load_json_usage() -> list:
    """Load demo app usage from usage.json if it exists."""
    if not os.path.exists(USAGE_JSON):
        return _default_usage()
    try:
        with open(USAGE_JSON) as f:
            data = json.load(f)
        # Support both list and dict with 'apps' key
        if isinstance(data, list):
            return data
        return data.get('apps', _default_usage())
    except (json.JSONDecodeError, IOError):
        return _default_usage()


def _default_usage() -> list:
    """Fallback usage data when no real data exists."""
    return [
        {'app_name': 'YouTube',   'minutes': 95},
        {'app_name': 'Instagram', 'minutes': 72},
        {'app_name': 'WhatsApp',  'minutes': 48},
        {'app_name': 'Chrome',    'minutes': 65},
        {'app_name': 'Netflix',   'minutes': 40},
        {'app_name': 'Twitter',   'minutes': 30},
    ]


def _estimate_pickups(total_minutes: float) -> int:
    """Estimate phone pickups based on total screen time."""
    if total_minutes <= 0:
        return 0
    # Rough heuristic: 1 pickup per ~8 minutes, ±20% randomness
    base = int(total_minutes / 8)
    return max(0, base + random.randint(-base // 5, base // 5))


# ── Productivity Score ─────────────────────────────────────────────

def get_productivity_score(user_id: int) -> dict:
    """
    Calculate a productivity score (0–100) and component breakdowns.
    """
    usage = get_usage_data(user_id)
    total = usage['total_minutes']

    # Thresholds (minutes)
    DISTRACTION_APPS = {'youtube', 'instagram', 'twitter', 'tiktok',
                        'facebook', 'netflix', 'snapchat', 'reddit'}

    distraction_mins = sum(
        a['minutes'] for a in usage['apps']
        if a['name'].lower() in DISTRACTION_APPS
    )
    productive_mins = max(0, total - distraction_mins)

    # Sub-scores (0–100)
    focus_score  = _clamp(100 - int((distraction_mins / max(total, 1)) * 100))
    breaks_score = _clamp(100 - max(0, int((total - 120) * 0.5)))  # Penalise >2h
    limits_score = _clamp(100 if total <= 180 else 100 - int((total - 180) * 0.4))

    overall = round((focus_score * 0.5 + breaks_score * 0.3 + limits_score * 0.2))

    return {
        'score':  overall,
        'focus':  focus_score,
        'breaks': breaks_score,
        'limits': limits_score,
    }


def _clamp(val: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, val))


# ── AI Suggestions ─────────────────────────────────────────────────

_SUGGESTION_POOL = [
    {
        'title': 'High Screen Time Detected',
        'desc':  'You\'ve exceeded 4 hours today. Try a 20-minute offline break right now.'
    },
    {
        'title': 'Morning Phone-Free Window',
        'desc':  'Avoid picking up your phone for the first 30 minutes after waking up.'
    },
    {
        'title': '20-20-20 Eye Relief Rule',
        'desc':  'Every 20 minutes, look at something 20 feet away for 20 seconds to reduce eye strain.'
    },
    {
        'title': 'Block Distracting Apps',
        'desc':  'Schedule focus sessions and block social media during your peak productive hours.'
    },
    {
        'title': 'Bedtime Screen Curfew',
        'desc':  'Set a screen curfew 1 hour before bed to improve your sleep quality.'
    },
    {
        'title': 'Replace Scroll Time',
        'desc':  'Swap 15 minutes of social media scrolling with a short walk or breathing exercise.'
    },
    {
        'title': 'Notification Diet',
        'desc':  'Turn off non-essential notifications to reduce involuntary phone pickups.'
    },
    {
        'title': 'Weekly Screen Review',
        'desc':  'Download your weekly report every Sunday to track progress over time.'
    },
]


def get_ai_suggestions(user_id: int) -> list:
    """
    Return contextual suggestions based on the user's usage data.
    """
    usage = get_usage_data(user_id)
    total = usage['total_minutes']
    suggestions = []

    # Always include high screen-time warning if applicable
    if total > 240:
        suggestions.append(_SUGGESTION_POOL[0])

    # Shuffle the rest and pick 3 more
    rest = [s for s in _SUGGESTION_POOL[1:] if s not in suggestions]
    random.shuffle(rest)
    suggestions.extend(rest[:3])

    return suggestions[:4]


# ── CSV Report ─────────────────────────────────────────────────────

def generate_report_csv(user_id: int, username: str) -> str:
    """
    Generate a CSV string report for the given user.
    """
    usage = get_usage_data(user_id)
    score = get_productivity_score(user_id)

    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header section
    writer.writerow(['Digital Detox Tracker — Daily Report'])
    writer.writerow(['Generated',  datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['User',       username])
    writer.writerow(['Date',       usage['date']])
    writer.writerow([])

    # Summary
    writer.writerow(['Summary'])
    writer.writerow(['Total Screen Time (min)', usage['total_minutes']])
    writer.writerow(['Phone Pickups',           usage['pickups']])
    writer.writerow(['Productivity Score',      f"{score['score']}%"])
    writer.writerow(['Focus Score',             f"{score['focus']}%"])
    writer.writerow(['Breaks Score',            f"{score['breaks']}%"])
    writer.writerow(['Limits Score',            f"{score['limits']}%"])
    writer.writerow([])

    # App breakdown
    writer.writerow(['App', 'Time (minutes)', 'Time (h:mm)'])
    for app in usage['apps']:
        mins = app['minutes']
        h, m = divmod(int(mins), 60)
        writer.writerow([app['name'], mins, f"{h}:{m:02d}"])

    return buf.getvalue()