"""
Delete duplicate loser posts from Everest MongoDB.

Posts to delete:
  1. קורס רכב ציבורי במכללת אוורסט: הדרך שלך לקריירה בטוחה ומתגמלת
     → replaced by: קורס רכב ציבורי במכללת אוורסט: הצעד הבא בקריירה שלך
  2. קורס מורה נהיגה מוסמך במכללת אוורסט - פתח דלת לקריירה מצליחה!
     → replaced by: קורס מורה נהיגה במכללת אוורסט: הצעד הבטוח לקריירה מצליחה

Run from project root: python scripts/delete_duplicates.py
Add --execute to actually delete (default is dry-run).
"""
import sys
import io
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import yaml
from publisher.mongodb_client import fetch_all_blog_posts, delete_blog_post

LOSERS = [
    "הדרך שלך לקריירה בטוחה ומתגמלת",   # רכב ציבורי loser (substring match)
    "מורה נהיגה מוסמך",                    # מורה נהיגה loser (substring match)
]


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Actually delete (default: dry-run)")
    args = parser.parse_args()

    config = load_config("config.everst.yaml")
    posts = fetch_all_blog_posts(config)

    to_delete = []
    for post in posts:
        title = post.get("title", "")
        for fragment in LOSERS:
            if fragment in title:
                to_delete.append(post)
                break

    if not to_delete:
        print("No matching posts found — nothing to delete.")
        return

    print(f"Posts to delete ({len(to_delete)}):")
    for p in to_delete:
        print(f"  _id: {p['_id']}")
        print(f"  title: {p['title']}")
        print()

    if not args.execute:
        print("[DRY RUN] Pass --execute to actually delete these posts.")
        return

    print("Deleting...")
    for p in to_delete:
        count = delete_blog_post(p["_id"], config)
        if count:
            print(f"  [OK] Deleted: {p['title']}")
        else:
            print(f"  [FAIL] Could not delete: {p['title']} (id: {p['_id']})")

    print("\nDone.")


if __name__ == "__main__":
    main()
