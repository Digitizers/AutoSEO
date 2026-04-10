"""
Audit MongoDB for Everest — list all blog posts with titles and slugs.
Run from project root: python scripts/mongo_audit.py
"""
import sys
import io
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import yaml
from publisher.mongodb_client import fetch_all_blog_posts


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def title_to_slug(title):
    """Approximate what the CMS would generate as a URL slug from a title."""
    import re
    return re.sub(r"\s+", "-", title.strip())


def main():
    config = load_config("config.everst.yaml")
    blog_url = config["site"]["blog_url"]  # https://www.ecstudy.co.il/programs

    print("=" * 70)
    print("MONGODB AUDIT — Everest blog posts")
    print("=" * 70)

    posts = fetch_all_blog_posts(config)
    posts_sorted = sorted(posts, key=lambda p: p.get("title", ""))

    print(f"\nTotal posts in MongoDB: {len(posts)}\n")

    for i, post in enumerate(posts_sorted, 1):
        title = post.get("title", "[no title]")
        slug = title_to_slug(title)
        created = post.get("createdAt", "?")
        print(f"{i:3d}. {title}")
        print(f"     URL: {blog_url}/{slug}")
        print(f"     Created: {created}")

    # Also dump to JSON for cross-referencing with GSC
    out = [
        {
            "_id": str(post.get("_id", "")),
            "title": post.get("title", ""),
            "slug": title_to_slug(post.get("title", "")),
            "url": f"{blog_url}/{title_to_slug(post.get('title', ''))}",
            "createdAt": str(post.get("createdAt", "")),
        }
        for post in posts_sorted
    ]
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "output", "everest_mongo_posts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved to {out_path}]")


if __name__ == "__main__":
    main()
