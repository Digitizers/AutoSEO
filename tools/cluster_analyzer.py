"""
Analyze existing blog posts and group into topical clusters.
Identifies pillar pages, satellite content, and cross-linking opportunities.
"""
import re
from collections import defaultdict


def extract_hebrew_keywords(title):
    """Extract significant Hebrew words from a title (2+ chars, skip stopwords)."""
    STOPWORDS = {
        'של', 'עם', 'על', 'את', 'הם', 'אל', 'כל', 'לא', 'זה', 'אך',
        'מה', 'כי', 'אם', 'גם', 'רק', 'כך', 'יש', 'אין', 'היה', 'הוא',
        'היא', 'הם', 'אנו', 'אנחנו', 'ב', 'ל', 'מ', 'ו', 'ה', 'כן',
        'אבל', 'רק', 'עוד', 'כבר', 'מאוד', 'כמה', 'בין', 'לפי', 'גדול',
    }
    words = re.findall(r'[\u0590-\u05FF]{2,}', title)
    return [w for w in words if w not in STOPWORDS]


def build_clusters(posts):
    """
    Group posts into topic clusters by shared root keywords.

    For Everest: "קורס" is always the first word → root = second word (the course type).
    For general sites: root = first significant word.

    posts: list of {_id, title, subtitle} from fetch_all_blog_posts()
    Returns: dict {cluster_root: [post_dict, ...]}
    """
    clusters = defaultdict(list)

    for post in posts:
        title = post.get("title", "")
        kws = extract_hebrew_keywords(title)
        if not kws:
            continue
        # For course sites: if title starts with "קורס", use the 2nd significant word as root
        root = kws[1] if len(kws) > 1 and kws[0] == 'קורס' else kws[0]
        clusters[root].append(post)

    # Merge singleton clusters into larger ones when they share keywords
    merged = {}
    for root, cluster_posts in clusters.items():
        if len(cluster_posts) == 1:
            post_kws = set(extract_hebrew_keywords(cluster_posts[0].get("title", "")))
            placed = False
            for other_root, other_posts in clusters.items():
                if other_root == root:
                    continue
                if other_root in post_kws and len(other_posts) > 1:
                    if other_root not in merged:
                        merged[other_root] = list(other_posts)
                    merged[other_root].extend(cluster_posts)
                    placed = True
                    break
            if not placed:
                merged[root] = cluster_posts
        else:
            if root not in merged:
                merged[root] = list(cluster_posts)

    return merged


def identify_pillar(cluster_posts):
    """
    The pillar page = the post with the shortest/most generic title.
    For Everest: "קורס מורה נהיגה" is the pillar, verbose variants are satellites.
    """
    return min(cluster_posts, key=lambda p: len(p.get("title", "")))


def analyze_clusters(posts, gsc_pages=None):
    """
    Full cluster analysis.

    Returns:
    {
        "clusters": {root: {"pillar": post, "satellites": [post, ...]}},
        "singletons": [post, ...],   # posts with no cluster match
        "recommendations": [str, ...]
    }
    """
    clusters = build_clusters(posts)
    result = {
        "clusters": {},
        "singletons": [],
        "recommendations": [],
    }

    for root, cluster_posts in clusters.items():
        if len(cluster_posts) == 1:
            result["singletons"].append(cluster_posts[0])
            continue

        pillar = identify_pillar(cluster_posts)
        satellites = [p for p in cluster_posts if p["_id"] != pillar["_id"]]

        result["clusters"][root] = {
            "pillar": pillar,
            "satellites": satellites,
        }

        result["recommendations"].append(
            f"Cluster '{root}': pillar='{pillar['title']}' | "
            f"{len(satellites)} satellite(s) — ensure all satellites link to pillar"
        )

    return result


def print_cluster_report(analysis):
    """Print human-readable cluster analysis to stdout."""
    print(f"\n{'='*70}")
    print("TOPICAL CLUSTER REPORT")
    print(f"{'='*70}")
    print(f"Clusters found: {len(analysis['clusters'])}")
    print(f"Singleton posts (no cluster): {len(analysis['singletons'])}")

    for root, cluster in analysis["clusters"].items():
        pillar = cluster["pillar"]
        sats = cluster["satellites"]
        print(f"\n[Cluster: {root}]")
        print(f"  PILLAR:    {pillar['title']}")
        for s in sats:
            print(f"  satellite: {s['title']}")

    if analysis["singletons"]:
        print("\n[Singleton posts — no cluster:]")
        for p in analysis["singletons"]:
            print(f"  - {p['title']}")

    print("\n[Recommendations:]")
    for r in analysis["recommendations"]:
        print(f"  • {r}")
