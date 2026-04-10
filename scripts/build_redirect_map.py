"""
Build the full 301 redirect map for Everest:
  - Dead GSC URLs (in GSC but not in MongoDB) → best matching live page
  - Duplicate live posts → winner

Run from project root: python scripts/build_redirect_map.py
"""
import sys
import io
import os
import json
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import yaml
from urllib.parse import unquote, urlparse
from publisher.mongodb_client import fetch_all_blog_posts


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def slug_from_url(url):
    return unquote(urlparse(url).path.rstrip("/").split("/")[-1])


def slug_from_title(title):
    return re.sub(r"\s+", "-", title.strip())


def hebrew_words(text):
    """Extract Hebrew words for overlap scoring."""
    return set(re.findall(r"[\u0590-\u05FF]+", text.lower()))


def best_match(dead_slug, live_posts):
    """Find the live post whose slug/title overlaps most with dead_slug."""
    dead_words = hebrew_words(dead_slug)
    best_score = 0
    best_post = None
    for post in live_posts:
        live_words = hebrew_words(post["slug"])
        if not dead_words or not live_words:
            continue
        overlap = len(dead_words & live_words)
        score = overlap / max(len(dead_words), len(live_words))
        if score > best_score:
            best_score = score
            best_post = post
    return best_post, best_score


def main():
    config = load_config("config.everst.yaml")
    blog_url = config["site"]["blog_url"]  # https://www.ecstudy.co.il/programs
    blog_path = urlparse(blog_url).path.rstrip("/")   # /programs

    # ── Load GSC data ─────────────────────────────────────────────────────────
    with open("output/everest_gsc_analysis.json", encoding="utf-8") as f:
        gsc = json.load(f)

    # Collect all blog URLs from GSC (page-level)
    gsc_blog_urls = set()
    for page in gsc["top_pages"]:
        u = page["url"]
        if blog_path in urlparse(u).path:
            gsc_blog_urls.add(u)
    for page in gsc["page2_opportunities"] + gsc["ctr_opportunities"]:
        u = page["url"]
        if blog_path in urlparse(u).path:
            gsc_blog_urls.add(u)
    # Also add all URLs from cannibalization data
    for item in gsc["cannibalization"]:
        for u in item["pages"]:
            if blog_path in urlparse(u).path:
                gsc_blog_urls.add(u)

    print(f"GSC blog URLs total: {len(gsc_blog_urls)}")

    # ── Load live MongoDB posts ───────────────────────────────────────────────
    raw_posts = fetch_all_blog_posts(config)
    live_posts = []
    for post in raw_posts:
        title = post.get("title", "")
        slug = slug_from_title(title)
        live_url = f"{blog_url}/{slug}"
        live_posts.append({
            "_id": str(post.get("_id", "")),
            "title": title,
            "slug": slug,
            "live_url": live_url,
            "live_path": f"{blog_path}/{slug}",
        })

    live_urls = {p["live_url"] for p in live_posts}
    live_paths = {p["live_path"] for p in live_posts}

    print(f"Live MongoDB posts: {len(live_posts)}")

    # ── Find dead URLs (in GSC but not in MongoDB) ────────────────────────────
    dead_urls = []
    for url in sorted(gsc_blog_urls):
        # Check if this URL corresponds to a live post (slug match)
        path = urlparse(url).path.rstrip("/")
        if path not in live_paths:
            dead_urls.append(url)

    print(f"Dead URLs (GSC but not in MongoDB): {len(dead_urls)}")

    # ── Build redirect map ────────────────────────────────────────────────────
    redirects = []

    # 1. Dead URLs → best matching live post
    print("\n--- DEAD URL REDIRECTS ---")
    for url in sorted(dead_urls):
        dead_slug = slug_from_url(url)
        match, score = best_match(dead_slug, live_posts)
        source_path = urlparse(url).path
        if match and score >= 0.25:
            dest_path = match["live_path"]
            redirects.append({
                "source": source_path,
                "destination": dest_path,
                "reason": f"dead page → best match (score {score:.2f})",
                "match_title": match["title"],
            })
            print(f"  {score:.2f}  {dead_slug}")
            print(f"        → {match['title']}")
        else:
            # Fall back to /programs (course listing)
            redirects.append({
                "source": source_path,
                "destination": blog_path,
                "reason": "dead page, no good match → programs listing",
                "match_title": "programs listing",
            })
            print(f"  {score:.2f}  {dead_slug}")
            print(f"        → [no match, → /programs]")

    # 2. Duplicate live posts — find pairs targeting the same core topic
    # Compare all pairs of live posts by Hebrew word overlap in their slugs
    print("\n--- DUPLICATE LIVE POST PAIRS ---")
    duplicate_pairs = []
    checked = set()
    for i, post_a in enumerate(live_posts):
        for j, post_b in enumerate(live_posts):
            if i >= j:
                continue
            pair_key = tuple(sorted([post_a["_id"], post_b["_id"]]))
            if pair_key in checked:
                continue
            checked.add(pair_key)

            words_a = hebrew_words(post_a["slug"])
            words_b = hebrew_words(post_b["slug"])
            if not words_a or not words_b:
                continue
            overlap = len(words_a & words_b)
            score = overlap / min(len(words_a), len(words_b))
            if score >= 0.6:
                duplicate_pairs.append((score, post_a, post_b))
                print(f"  score {score:.2f}")
                print(f"    A: {post_a['title']}")
                print(f"    B: {post_b['title']}")

    # For each duplicate pair, decide winner by GSC impressions
    # Build a quick GSC lookup by path
    gsc_by_path = {}
    for page in gsc["top_pages"] + gsc["page2_opportunities"] + gsc["ctr_opportunities"]:
        path = urlparse(page["url"]).path.rstrip("/")
        if path not in gsc_by_path or page["impressions"] > gsc_by_path[path]["impressions"]:
            gsc_by_path[path] = page

    print("\n--- DUPLICATE RESOLUTION ---")
    for score, post_a, post_b in duplicate_pairs:
        impr_a = gsc_by_path.get(post_a["live_path"], {}).get("impressions", 0)
        impr_b = gsc_by_path.get(post_b["live_path"], {}).get("impressions", 0)

        if impr_a >= impr_b:
            winner, loser = post_a, post_b
            winner_impr, loser_impr = impr_a, impr_b
        else:
            winner, loser = post_b, post_a
            winner_impr, loser_impr = impr_b, impr_a

        print(f"  KEEP:   {winner['title']}  ({winner_impr} impr)")
        print(f"  DELETE: {loser['title']}  ({loser_impr} impr)")
        print(f"  Redirect: {loser['live_path']} → {winner['live_path']}")

        redirects.append({
            "source": loser["live_path"],
            "destination": winner["live_path"],
            "reason": f"duplicate, loser ({loser_impr} impr) → winner ({winner_impr} impr)",
            "match_title": winner["title"],
            "delete_from_mongo": loser["_id"],
            "delete_title": loser["title"],
        })

    # ── Output ────────────────────────────────────────────────────────────────
    out_path = "output/everest_redirects.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(redirects, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved redirect map to {out_path}]")
    print(f"Total redirects: {len(redirects)}")

    # Print Next.js format preview
    print("\n--- NEXT.JS redirects() PREVIEW ---")
    for r in redirects:
        print(f"  {{ source: '{r['source']}', destination: '{r['destination']}', permanent: true }},")


if __name__ == "__main__":
    main()
