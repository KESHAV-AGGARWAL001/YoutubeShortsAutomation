"""
carousel_dashboard.py — Carousel Status Dashboard

Shows all pending and uploaded carousels with their status,
creation dates, and media IDs.

Usage:
  python carousel_dashboard.py
"""

import os
import json
from datetime import datetime

CAROUSELS_DIR = os.path.join(os.path.dirname(__file__), "carousels")
REGISTRY_PATH = os.path.join(CAROUSELS_DIR, "carousel_registry.json")


def load_registry():
    """Load the carousel registry."""
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": [], "uploaded": []}


def format_date(date_str):
    """Convert ISO timestamp to readable date."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str or "?"


def main():
    registry = load_registry()
    pending = registry.get("pending", [])
    uploaded = registry.get("uploaded", [])

    # ── Header ──
    W = 58
    print()
    print("╔" + "═" * W + "╗")
    print("║" + "  🎠 IronMindset — Carousel Dashboard".center(W) + "║")
    print("╠" + "═" * W + "╣")

    # ── Pending Carousels ──
    if pending:
        print("║" + f"  PENDING UPLOAD ({len(pending)})".ljust(W) + "║")
        print("╠" + "═" * W + "╣")
        for c in pending:
            title = c.get("title", "Untitled")[:45]
            ctype = c.get("type", "?")
            cat   = c.get("category", "?").replace("_", " ").title()
            slides = c.get("total_slides", "?")
            created = format_date(c.get("created_at", ""))

            print("║" + f"  🖼  {title}".ljust(W) + "║")
            print("║" + f"     Type: {ctype} | Cat: {cat} | Slides: {slides}".ljust(W) + "║")
            print("║" + f"     Status: ⏳ pending | Created: {created}".ljust(W) + "║")
            print("╠" + "═" * W + "╣")
    else:
        print("║" + "  No pending carousels".ljust(W) + "║")
        print("╠" + "═" * W + "╣")

    # ── Uploaded Carousels ──
    if uploaded:
        print("║" + f"  UPLOADED ({len(uploaded)})".ljust(W) + "║")
        print("╠" + "═" * W + "╣")
        # Show last 5 uploaded
        for c in reversed(uploaded[-5:]):
            title = c.get("title", "Untitled")[:45]
            mid = c.get("media_id", "?")
            u_date = format_date(c.get("uploaded_at", ""))

            print("║" + f"  ✅ {title}".ljust(W) + "║")
            print("║" + f"     Type: {c.get('type','?')} | Uploaded: {u_date}".ljust(W) + "║")
            print("║" + f"     Media ID: {mid}".ljust(W) + "║")
            print("╠" + "═" * W + "╣")
    else:
        print("║" + "  No uploaded carousels yet".ljust(W) + "║")
        print("╠" + "═" * W + "╣")

    # ── Quick Stats ──
    total_p = len(pending)
    total_u = len(uploaded)
    print("║" + f"  Stats: {total_p} pending | {total_u} uploaded".ljust(W) + "║")
    print("╚" + "═" * W + "╝")

    # ── Helpful Commands ──
    print(f"\n  Commands:")
    print(f"    python generate_carousel.py          # create new carousel")
    print(f"    python upload_carousel.py --list     # show all pending")
    print(f"    python upload_carousel.py --id <id>  # upload specific carousel")
    print()


if __name__ == "__main__":
    main()
