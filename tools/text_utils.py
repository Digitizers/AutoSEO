"""Shared text utility functions used across the SEO engine."""
import re


def slugify_hebrew(title):
    """
    Convert a Hebrew post title to a URL slug matching Everest CMS logic.
    Everest uses the post title directly as the slug, with spaces → hyphens.

    'קורס מורה נהיגה' → 'קורס-מורה-נהיגה'
    """
    # Strip common site name suffixes: "Title | Site", "Title – Site", "Title — Site", "Title - Site"
    title = re.split(r'\s*[|–—]\s*|\s+-\s+', title)[0].strip()
    # Replace any non-Hebrew, non-Latin, non-digit character (spaces, punctuation) with hyphens
    slug = re.sub(r'[^\u0590-\u05FFa-zA-Z0-9]+', '-', title)
    slug = slug.strip('-')
    return slug
