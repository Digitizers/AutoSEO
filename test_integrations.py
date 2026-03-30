"""
test_integrations.py

Smoke tests: verify imports, class structures, and basic publisher behaviour
without real credentials or live network calls.

Run locally:
    pytest test_integrations.py -v
    pytest test_integrations.py -v --cov=publishers --cov=tools --cov-report=term-missing

Note: tests for optional heavy dependencies (playwright, pytrends,
google-api-python-client, Pillow) are skipped automatically when those
packages are not installed.
"""

import importlib
import inspect

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _available(module_name: str) -> bool:
    """Return True if a top-level module is importable."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Fake configs — nested exactly as each publisher expects them
# ---------------------------------------------------------------------------

_WP_CONFIG = {
    "platform": "wordpress",
    "wordpress": {
        "site_url": "https://example.com",
        "auth_method": "app_password",
        "username": "admin",
        "app_password": "fake-pw",
    },
}

_WIX_CONFIG = {
    "platform": "wix",
    "wix": {
        "api_key": "fake-key",
        "site_id": "fake-site-id",
    },
}

_SHOPIFY_CONFIG = {
    "platform": "shopify",
    "shopify": {
        "store_domain": "mystore.myshopify.com",
        "admin_api_token": "fake-token",
    },
}

_WOO_CONFIG = {
    "platform": "woocommerce",
    "woocommerce": {
        "site_url": "https://example.com",
        "consumer_key": "ck_fake",
        "consumer_secret": "cs_fake",
    },
}

_ALL_CONFIGS = [
    ("publishers.wordpress.WordPressPublisher", _WP_CONFIG),
    ("publishers.wix.WixPublisher", _WIX_CONFIG),
    ("publishers.shopify.ShopifyPublisher", _SHOPIFY_CONFIG),
    ("publishers.woocommerce.WooCommercePublisher", _WOO_CONFIG),
]

_REQUIRED_METHODS = ("fetch_posts", "publish_post", "update_post", "test_connection")


# ===========================================================================
# Publisher — import tests
# ===========================================================================


class TestPublisherImports:
    """All publisher modules must import without errors."""

    def test_base_is_abstract(self):
        from publishers.base import BasePlatformPublisher
        assert inspect.isabstract(BasePlatformPublisher)

    def test_factory_callable(self):
        from publishers.factory import get_publisher
        assert callable(get_publisher)

    def test_wordpress(self):
        from publishers.wordpress import WordPressPublisher  # noqa: F401

    def test_wix(self):
        from publishers.wix import WixPublisher  # noqa: F401

    def test_shopify(self):
        from publishers.shopify import ShopifyPublisher  # noqa: F401

    def test_woocommerce(self):
        from publishers.woocommerce import WooCommercePublisher  # noqa: F401


# ===========================================================================
# Publisher — instantiation (no network calls)
# ===========================================================================


class TestPublisherInstantiation:
    """Publishers must initialise with fake credentials without making network calls."""

    def test_wordpress(self):
        from publishers.wordpress import WordPressPublisher
        assert WordPressPublisher(_WP_CONFIG) is not None

    def test_wix(self):
        from publishers.wix import WixPublisher
        assert WixPublisher(_WIX_CONFIG) is not None

    def test_shopify(self):
        from publishers.shopify import ShopifyPublisher
        assert ShopifyPublisher(_SHOPIFY_CONFIG) is not None

    def test_woocommerce(self):
        from publishers.woocommerce import WooCommercePublisher
        assert WooCommercePublisher(_WOO_CONFIG) is not None


# ===========================================================================
# Publisher — interface contract (parametrized)
# ===========================================================================


@pytest.mark.parametrize("cls_path,config", _ALL_CONFIGS)
def test_publisher_interface(cls_path: str, config: dict):
    """Every publisher must expose the four BasePlatformPublisher abstract methods."""
    module_path, cls_name = cls_path.rsplit(".", 1)
    cls = getattr(importlib.import_module(module_path), cls_name)
    instance = cls(config)
    for method in _REQUIRED_METHODS:
        assert hasattr(instance, method), f"{cls_name} is missing '{method}'"
        assert callable(getattr(instance, method)), f"{cls_name}.{method} is not callable"


# ===========================================================================
# Factory
# ===========================================================================


@pytest.mark.parametrize("expected_cls,config", [
    ("WordPressPublisher", _WP_CONFIG),
    ("WixPublisher", _WIX_CONFIG),
    ("ShopifyPublisher", _SHOPIFY_CONFIG),
    ("WooCommercePublisher", _WOO_CONFIG),
])
def test_factory_routes_correctly(expected_cls: str, config: dict):
    from publishers.factory import get_publisher
    pub = get_publisher(config)
    assert type(pub).__name__ == expected_cls


def test_factory_unknown_platform_raises():
    from publishers.factory import get_publisher
    with pytest.raises(ValueError):
        get_publisher({"platform": "nonexistent_xyz"})


# ===========================================================================
# WordPress publisher — mocked HTTP
# ===========================================================================


class TestWordPressPublisher:
    _BASE = "https://example.com"

    def _pub(self):
        from publishers.wordpress import WordPressPublisher
        return WordPressPublisher(_WP_CONFIG)

    def test_trailing_slash_stripped(self):
        from publishers.wordpress import WordPressPublisher
        cfg = {
            **_WP_CONFIG,
            "wordpress": {**_WP_CONFIG["wordpress"], "site_url": "https://example.com/"},
        }
        assert WordPressPublisher(cfg)._base() == "https://example.com"

    def test_fetch_posts(self, requests_mock):
        requests_mock.get(
            f"{self._BASE}/wp-json/wp/v2/posts",
            json=[{
                "id": 1,
                "title": {"rendered": "Hello"},
                "excerpt": {"rendered": "Excerpt"},
                "link": "https://example.com/hello",
                "date": "2024-01-01T00:00:00",
                "status": "publish",
            }],
        )
        posts = self._pub().fetch_posts(limit=5)
        assert isinstance(posts, list)
        assert posts[0]["_id"] == "1"
        assert posts[0]["title"] == "Hello"

    def test_publish_post_returns_string_id(self, requests_mock):
        requests_mock.post(
            f"{self._BASE}/wp-json/wp/v2/posts",
            json={"id": 42, "link": "https://example.com/new-post"},
        )
        post_id = self._pub().publish_post({"title": "New", "content": "Body"})
        assert post_id == "42"

    def test_update_post_success(self, requests_mock):
        requests_mock.post(f"{self._BASE}/wp-json/wp/v2/posts/42", json={"id": 42})
        assert self._pub().update_post("42", {"title": "Updated"}) is True

    def test_test_connection_ok(self, requests_mock):
        requests_mock.get(
            f"{self._BASE}/wp-json/wp/v2/users/me",
            json={"id": 1, "name": "Admin"},
        )
        ok, msg = self._pub().test_connection()
        assert ok is True
        assert "Admin" in msg

    def test_test_connection_auth_failure(self, requests_mock):
        requests_mock.get(
            f"{self._BASE}/wp-json/wp/v2/users/me",
            status_code=401,
            json={"code": "rest_not_logged_in"},
        )
        ok, _ = self._pub().test_connection()
        assert ok is False


# ===========================================================================
# Wix publisher — mocked HTTP
# ===========================================================================


class TestWixPublisher:
    _BASE = "https://www.wixapis.com"

    def _pub(self):
        from publishers.wix import WixPublisher
        return WixPublisher(_WIX_CONFIG)

    def test_headers_contain_api_key_and_site_id(self):
        headers = self._pub()._headers()
        assert headers.get("Authorization") == "fake-key"
        assert headers.get("wix-site-id") == "fake-site-id"

    def test_fetch_posts(self, requests_mock):
        requests_mock.post(
            f"{self._BASE}/blog/v3/posts/query",
            json={
                "posts": [{
                    "id": "abc",
                    "title": "Wix Post",
                    "excerpt": "Short summary",
                    "url": {"base": "https://mysite.com", "path": "/post/abc"},
                    "firstPublishedDate": "2024-01-01",
                    "status": "PUBLISHED",
                }]
            },
        )
        posts = self._pub().fetch_posts(limit=5)
        assert isinstance(posts, list)
        assert posts[0]["_id"] == "abc"
        assert posts[0]["title"] == "Wix Post"

    def test_test_connection_ok(self, requests_mock):
        requests_mock.post(f"{self._BASE}/blog/v3/posts/query", json={"posts": []})
        ok, _ = self._pub().test_connection()
        assert ok is True

    def test_test_connection_failure(self, requests_mock):
        requests_mock.post(f"{self._BASE}/blog/v3/posts/query", status_code=403, json={})
        ok, _ = self._pub().test_connection()
        assert ok is False


# ===========================================================================
# Shopify publisher — mocked HTTP
# ===========================================================================


class TestShopifyPublisher:
    _BASE = "https://mystore.myshopify.com/admin/api/2024-01"

    def _pub(self):
        from publishers.shopify import ShopifyPublisher
        return ShopifyPublisher(_SHOPIFY_CONFIG)

    def test_base_url(self):
        assert self._pub()._base() == self._BASE

    def test_headers_contain_token(self):
        headers = self._pub()._headers()
        assert headers.get("X-Shopify-Access-Token") == "fake-token"

    def test_test_connection_ok(self, requests_mock):
        requests_mock.get(
            f"{self._BASE}/shop.json",
            json={"shop": {"id": 1, "name": "My Test Store"}},
        )
        ok, msg = self._pub().test_connection()
        assert ok is True
        assert "My Test Store" in msg

    def test_test_connection_failure(self, requests_mock):
        requests_mock.get(f"{self._BASE}/shop.json", status_code=401, json={})
        ok, _ = self._pub().test_connection()
        assert ok is False


# ===========================================================================
# WooCommerce publisher — mocked HTTP
# ===========================================================================


class TestWooCommercePublisher:
    _BASE = "https://example.com"

    def _pub(self):
        from publishers.woocommerce import WooCommercePublisher
        return WooCommercePublisher(_WOO_CONFIG)

    def test_base_url(self):
        assert self._pub()._base() == self._BASE

    def test_test_connection_ok(self, requests_mock):
        requests_mock.get(
            f"{self._BASE}/wp-json/wc/v3/system_status",
            json={"environment": {"wp_version": "6.4"}},
        )
        ok, msg = self._pub().test_connection()
        assert ok is True
        assert "WooCommerce" in msg

    def test_test_connection_failure(self, requests_mock):
        requests_mock.get(f"{self._BASE}/wp-json/wc/v3/system_status", status_code=401, json={})
        ok, _ = self._pub().test_connection()
        assert ok is False

    def test_publish_post_returns_string_id(self, requests_mock):
        requests_mock.post(
            f"{self._BASE}/wp-json/wc/v3/products",
            json={"id": 99, "name": "Test Product"},
        )
        post_id = self._pub().publish_post({"name": "Test Product", "type": "simple"})
        assert post_id == "99"

    def test_upload_image_skipped_without_wp_credentials(self):
        """upload_image returns None when no WP username/password are configured."""
        result = self._pub().upload_image(b"fake-image-bytes", "test.jpg")
        assert result is None


# ===========================================================================
# Tools — import smoke tests
# ===========================================================================


class TestToolImports:
    """Verify lightweight tool modules import cleanly."""

    def test_autocomplete(self):
        from tools.autocomplete import get_autocomplete, get_autocomplete_expanded
        assert callable(get_autocomplete)
        assert callable(get_autocomplete_expanded)

    def test_blog_analyzer(self):
        from tools.blog_analyzer import (
            analyze_blog_post, analyze_all_posts, discover_blog_posts,
        )
        assert callable(analyze_blog_post)
        assert callable(analyze_all_posts)
        assert callable(discover_blog_posts)

    def test_competitor_analyzer(self):
        from tools.competitor_analyzer import (
            analyze_page, analyze_competitors, summarize_competitor_patterns,
        )
        assert callable(analyze_page)
        assert callable(analyze_competitors)
        assert callable(summarize_competitor_patterns)

    def test_pagespeed(self):
        from tools.pagespeed import check_page_speed, check_pages_speed, format_cwv_summary
        assert callable(check_page_speed)
        assert callable(check_pages_speed)
        assert callable(format_cwv_summary)

    def test_trends(self):
        pytest.importorskip("pytrends", reason="pytrends not installed")
        from tools.trends import get_trends_data
        assert callable(get_trends_data)

    def test_search_console(self):
        pytest.importorskip("googleapiclient", reason="google-api-python-client not installed")
        from tools.search_console import fetch_gsc_performance, classify_page_seo
        assert callable(fetch_gsc_performance)
        assert callable(classify_page_seo)

    def test_serp_scraper(self):
        pytest.importorskip("playwright", reason="playwright not installed")
        pytest.importorskip("playwright_stealth", reason="playwright-stealth not installed")
        from tools.serp_scraper import scrape_serp
        assert callable(scrape_serp)

    def test_product_pipeline(self):
        # product_pipeline depends on both Pillow and tools.search_console (→ googleapiclient)
        pytest.importorskip("PIL", reason="Pillow not installed")
        pytest.importorskip("googleapiclient", reason="google-api-python-client not installed")
        from tools.product_pipeline import load_product_history, download_image, brand_product_image
        assert callable(load_product_history)
        assert callable(download_image)
        assert callable(brand_product_image)
