"""
Pull full GSC data for Everest (ecstudy.co.il) and print a structured analysis.
Run from project root: python scripts/gsc_analysis.py
"""
import sys
import io
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import yaml
from tools.search_console import (
    fetch_gsc_performance,
    fetch_page_queries,
    classify_page_seo,
    match_post_to_gsc_url,
)
from publisher.mongodb_client import fetch_all_blog_posts


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config("config.everst.yaml")
    domain = config["site"]["domain"]
    blog_url = config["site"]["blog_url"]

    print("=" * 70)
    print("GSC FULL ANALYSIS — Everest (ecstudy.co.il)")
    print("=" * 70)

    # ── Fetch raw data ────────────────────────────────────────────────────────
    print("\n[1] Fetching page-level performance (90 days)...")
    perf_90 = fetch_gsc_performance(config, days=90)

    print("\n[2] Fetching page+query data (90 days)...")
    page_queries = fetch_page_queries(config, days=90)

    print("\n[3] Fetching page-level performance (28 days) for trend comparison...")
    perf_28 = fetch_gsc_performance(config, days=28)

    # ── Site summary ─────────────────────────────────────────────────────────
    total_clicks_90    = sum(v["clicks"] for v in perf_90.values())
    total_impr_90      = sum(v["impressions"] for v in perf_90.values())
    total_clicks_28    = sum(v["clicks"] for v in perf_28.values())
    total_impr_28      = sum(v["impressions"] for v in perf_28.values())
    all_positions_90   = [v["position"] for v in perf_90.values() if v.get("position")]
    avg_pos_90         = round(sum(all_positions_90) / len(all_positions_90), 1) if all_positions_90 else 0
    avg_ctr_90         = round(sum(v["ctr"] for v in perf_90.values()) / len(perf_90) * 100, 2) if perf_90 else 0

    print("\n" + "=" * 70)
    print("SITE SUMMARY")
    print("=" * 70)
    print(f"  Pages tracked (90d):        {len(perf_90)}")
    print(f"  Total clicks  90d:          {total_clicks_90:,}")
    print(f"  Total clicks  28d:          {total_clicks_28:,}")
    print(f"  Total impr    90d:          {total_impr_90:,}")
    print(f"  Total impr    28d:          {total_impr_28:,}")
    print(f"  Avg position  90d:          {avg_pos_90}")
    print(f"  Avg CTR       90d:          {avg_ctr_90}%")

    # ── Classify every blog page ──────────────────────────────────────────────
    from urllib.parse import urlparse
    blog_path = urlparse(blog_url).path.rstrip("/")

    blog_pages = {url: data for url, data in perf_90.items()
                  if blog_path in urlparse(url).path}
    other_pages = {url: data for url, data in perf_90.items()
                   if blog_path not in urlparse(url).path}

    print(f"\n  Blog posts in GSC:           {len(blog_pages)}")
    print(f"  Non-blog pages in GSC:       {len(other_pages)}")

    classified = {}
    for url, data in perf_90.items():
        ctx = classify_page_seo(url, perf_90, page_queries, config)
        classified[url] = {**data, **ctx}

    cats = {}
    for url, d in classified.items():
        if blog_path in urlparse(url).path:
            cat = d["category"]
            cats[cat] = cats.get(cat, 0) + 1

    print("\n  Blog post classification (90d):")
    for cat, count in sorted(cats.items()):
        print(f"    {cat}: {count}")

    # ── Top performers ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("TOP 20 PAGES BY CLICKS (90d)")
    print("=" * 70)
    top_by_clicks = sorted(perf_90.items(), key=lambda x: x[1]["clicks"], reverse=True)[:20]
    for url, d in top_by_clicks:
        cat = classified.get(url, {}).get("category", "?")
        print(f"  [{cat:18s}] {d['clicks']:5d} clk | {d['impressions']:6d} impr | "
              f"pos {d['position']:5.1f} | CTR {d['ctr']*100:4.1f}%")
        print(f"    {url}")
        queries = page_queries.get(url, [])[:3]
        for q in queries:
            print(f"      > '{q['query']}' ({q['clicks']} clk, pos {q['position']})")

    # ── Page2 opportunities ───────────────────────────────────────────────────
    page2 = [(url, d) for url, d in classified.items()
             if d["category"] == "page2_opportunity"
             and blog_path in urlparse(url).path]
    page2.sort(key=lambda x: x[1]["impressions"], reverse=True)

    print("\n" + "=" * 70)
    print(f"PAGE 2 OPPORTUNITIES — {len(page2)} posts (pos 11-30, impr >= 20)")
    print("(Highest ROI: small push gets them to page 1)")
    print("=" * 70)
    for url, d in page2[:20]:
        print(f"  pos {d['position']:5.1f} | {d['impressions']:6d} impr | {d['clicks']:4d} clk | "
              f"CTR {d['ctr']*100:4.1f}%")
        print(f"    {url}")
        queries = page_queries.get(url, [])[:3]
        for q in queries:
            print(f"      &gt; '{q['query']}' ({q['impressions']} impr, pos {q['position']})")

    # ── CTR opportunities ─────────────────────────────────────────────────────
    ctr_opps = [(url, d) for url, d in classified.items()
                if d["category"] == "ctr_opportunity"
                and blog_path in urlparse(url).path]
    ctr_opps.sort(key=lambda x: x[1]["impressions"], reverse=True)

    print("\n" + "=" * 70)
    print(f"CTR OPPORTUNITIES — {len(ctr_opps)} posts (page 1, CTR < 3%, impr >= 50)")
    print("(Ranking well but not getting clicked — meta desc fix needed)")
    print("=" * 70)
    for url, d in ctr_opps[:20]:
        print(f"  pos {d['position']:5.1f} | {d['impressions']:6d} impr | {d['clicks']:4d} clk | "
              f"CTR {d['ctr']*100:4.1f}%")
        print(f"    {url}")
        queries = page_queries.get(url, [])[:3]
        for q in queries:
            print(f"      &gt; '{q['query']}' ({q['impressions']} impr, CTR {q['ctr_pct']}%)")

    # ── Low performers ────────────────────────────────────────────────────────
    low = [(url, d) for url, d in classified.items()
           if d["category"] == "low_performer"
           and blog_path in urlparse(url).path]
    low.sort(key=lambda x: x[1]["impressions"], reverse=True)

    print("\n" + "=" * 70)
    print(f"LOW PERFORMERS — {len(low)} posts (have GSC data but ranking poorly)")
    print("=" * 70)
    for url, d in low[:15]:
        print(f"  pos {d['position']:5.1f} | {d['impressions']:5d} impr | {d['clicks']:3d} clk")
        print(f"    {url}")

    # ── Not indexed ───────────────────────────────────────────────────────────
    # These are posts in MongoDB but absent from GSC entirely
    print("\n" + "=" * 70)
    print("POSTS NOT IN GSC (not indexed or no impressions)")
    print("=" * 70)
    try:
        raw_posts = fetch_all_blog_posts(config)
        not_in_gsc = []
        for post in raw_posts:
            title = post.get("title", "")
            url, _ = match_post_to_gsc_url(title, perf_90, config)
            if not url:
                not_in_gsc.append(title)
        print(f"  {len(not_in_gsc)} posts have no GSC match:")
        for t in not_in_gsc[:30]:
            print(f"    - {t}")
    except Exception as e:
        print(f"  [warn] Could not fetch MongoDB posts: {e}")

    # ── Zero-click pages ──────────────────────────────────────────────────────
    zero_click_blog = [(url, d) for url, d in blog_pages.items()
                       if d["clicks"] == 0 and d["impressions"] > 0]
    zero_click_blog.sort(key=lambda x: x[1]["impressions"], reverse=True)

    print("\n" + "=" * 70)
    print(f"ZERO-CLICK BLOG PAGES — {len(zero_click_blog)} pages (impressions > 0 but 0 clicks)")
    print("=" * 70)
    for url, d in zero_click_blog[:20]:
        print(f"  pos {d['position']:5.1f} | {d['impressions']:5d} impr | CTR {d['ctr']*100:4.1f}%")
        print(f"    {url}")

    # ── Top queries site-wide ─────────────────────────────────────────────────
    all_queries = {}
    for url, queries in page_queries.items():
        for q in queries:
            key = q["query"]
            if key not in all_queries:
                all_queries[key] = {"clicks": 0, "impressions": 0, "pages": []}
            all_queries[key]["clicks"] += q["clicks"]
            all_queries[key]["impressions"] += q["impressions"]
            all_queries[key]["pages"].append(url)

    top_queries_by_impr = sorted(all_queries.items(), key=lambda x: x[1]["impressions"], reverse=True)[:30]

    print("\n" + "=" * 70)
    print("TOP 30 QUERIES BY IMPRESSIONS (site-wide)")
    print("=" * 70)
    for query, data in top_queries_by_impr:
        n_pages = len(data["pages"])
        flag = " !! CANNIBALIZED" if n_pages > 1 else ""
        print(f"  {data['impressions']:6d} impr | {data['clicks']:4d} clk | "
              f"{n_pages} page(s){flag}")
        print(f"    '{query}'")

    # ── Cannibalization check ─────────────────────────────────────────────────
    cannibalized = [(q, d) for q, d in all_queries.items() if len(d["pages"]) > 1]
    cannibalized.sort(key=lambda x: x[1]["impressions"], reverse=True)

    print("\n" + "=" * 70)
    print(f"KEYWORD CANNIBALIZATION — {len(cannibalized)} queries fought over by multiple pages")
    print("=" * 70)
    for query, data in cannibalized[:20]:
        print(f"  '{query}' ({data['impressions']} impr)")
        for page_url in data["pages"]:
            pd = perf_90.get(page_url, {})
            print(f"    pos {pd.get('position', '?'):5.1f} | {pd.get('clicks', 0)} clk — {page_url}")

    # ── Save raw data for plan writing ────────────────────────────────────────
    out = {
        "summary": {
            "pages_tracked_90d": len(perf_90),
            "total_clicks_90d": total_clicks_90,
            "total_clicks_28d": total_clicks_28,
            "total_impressions_90d": total_impr_90,
            "total_impressions_28d": total_impr_28,
            "avg_position_90d": avg_pos_90,
            "avg_ctr_pct_90d": avg_ctr_90,
            "blog_pages_in_gsc": len(blog_pages),
            "classification": cats,
        },
        "top_pages": [
            {
                "url": url,
                "clicks": d["clicks"],
                "impressions": d["impressions"],
                "position": round(d["position"], 1),
                "ctr_pct": round(d["ctr"] * 100, 1),
                "category": classified.get(url, {}).get("category", "?"),
                "top_queries": [q["query"] for q in page_queries.get(url, [])[:5]],
            }
            for url, d in top_by_clicks[:30]
        ],
        "page2_opportunities": [
            {
                "url": url,
                "impressions": d["impressions"],
                "clicks": d["clicks"],
                "position": round(d["position"], 1),
                "ctr_pct": round(d["ctr"] * 100, 1),
                "top_queries": [q["query"] for q in page_queries.get(url, [])[:5]],
            }
            for url, d in page2[:25]
        ],
        "ctr_opportunities": [
            {
                "url": url,
                "impressions": d["impressions"],
                "clicks": d["clicks"],
                "position": round(d["position"], 1),
                "ctr_pct": round(d["ctr"] * 100, 1),
                "top_queries": [q["query"] for q in page_queries.get(url, [])[:5]],
            }
            for url, d in ctr_opps[:25]
        ],
        "cannibalization": [
            {
                "query": query,
                "impressions": data["impressions"],
                "clicks": data["clicks"],
                "pages": data["pages"],
            }
            for query, data in cannibalized[:30]
        ],
    }

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "output", "everest_gsc_analysis.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n\n[Saved raw analysis to {out_path}]")
    print("=" * 70)


if __name__ == "__main__":
    main()
