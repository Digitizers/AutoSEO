"""WordPress REST API v2 publisher.

Supported auth methods (set via config['wordpress']['auth_method']):
  app_password  — HTTP Basic Auth with a WP Application Password (default, WP 5.6+)
  password      — HTTP Basic Auth with the user's regular login password
  bearer        — Bearer token (e.g. JWT Auth plugin or custom token)
"""
import requests
from publishers.base import BasePlatformPublisher


class WordPressPublisher(BasePlatformPublisher):
    def _cfg(self) -> dict:
        return self.config["wordpress"]

    def _base(self) -> str:
        return self._cfg()["site_url"].rstrip("/")

    # ------------------------------------------------------------------
    # Auth helpers — all requests go through _rq() which applies the
    # correct auth regardless of method.
    # ------------------------------------------------------------------

    def _rq(self, method: str, path: str, extra_headers: dict | None = None, **kwargs) -> requests.Response:
        """Make an authenticated request to the WP REST API."""
        cfg = self._cfg()
        auth_method = cfg.get("auth_method", "app_password")
        headers = dict(extra_headers or {})

        if auth_method == "bearer":
            headers["Authorization"] = f"Bearer {cfg.get('token', '')}"
            return requests.request(method, f"{self._base()}{path}", headers=headers, **kwargs)
        else:
            # app_password or password — both use HTTP Basic Auth
            password = cfg.get("app_password") or cfg.get("password", "")
            return requests.request(
                method, f"{self._base()}{path}",
                auth=(cfg["username"], password),
                headers=headers or None,
                **kwargs,
            )

    # ------------------------------------------------------------------
    # Image upload → WP Media Library
    # ------------------------------------------------------------------

    def _upload_to_media_library(self, image_bytes: bytes, filename: str = "image.jpg") -> tuple[str, int] | None:
        """Upload image to WP media library.
        Returns (source_url, media_id) on success, None on failure.
        """
        try:
            resp = self._rq(
                "POST", "/wp-json/wp/v2/media",
                extra_headers={
                    "Content-Type": "image/jpeg",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
                data=image_bytes,
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                return data.get("source_url", ""), data.get("id")
            print(f"  [wp] Media upload failed: HTTP {resp.status_code} {resp.text[:200]}")
        except Exception as exc:
            print(f"  [wp] Media upload error: {exc}")
        return None

    def upload_image(self, image_bytes: bytes, filename: str = "image.jpg") -> str | None:
        result = self._upload_to_media_library(image_bytes, filename)
        return result[0] if result else None

    # ------------------------------------------------------------------
    # BasePlatformPublisher interface
    # ------------------------------------------------------------------

    def fetch_posts(self, limit: int = 50) -> list[dict]:
        resp = self._rq(
            "GET", "/wp-json/wp/v2/posts",
            params={"per_page": min(limit, 100), "status": "publish"},
            timeout=20,
        )
        resp.raise_for_status()
        return [
            {
                "_id": str(p["id"]),
                "title": p.get("title", {}).get("rendered", ""),
                "subtitle": p.get("excerpt", {}).get("rendered", ""),
                "url": p.get("link", ""),
                "created_at": p.get("date", ""),
                "status": p.get("status", "publish"),
            }
            for p in resp.json()
        ]

    def publish_post(self, post_data: dict) -> str:
        # Upload image bytes if provided, set as featured image
        featured_media_id = None
        image_bytes = post_data.pop("image_bytes", None)
        if image_bytes:
            result = self._upload_to_media_library(image_bytes)
            if result:
                _, featured_media_id = result

        payload = {
            "title": post_data.get("title", ""),
            "content": post_data.get("content") or post_data.get("body", ""),
            "excerpt": post_data.get("subtitle", ""),
            "status": "publish",
        }
        if featured_media_id:
            payload["featured_media"] = featured_media_id

        resp = self._rq("POST", "/wp-json/wp/v2/posts", json=payload, timeout=30)
        resp.raise_for_status()
        return str(resp.json()["id"])

    def update_post(self, post_id: str, update_data: dict) -> bool:
        # Upload image bytes if provided, set as featured image
        image_bytes = update_data.pop("image_bytes", None)
        if image_bytes:
            result = self._upload_to_media_library(image_bytes)
            if result:
                _, media_id = result
                update_data["featured_media"] = media_id

        resp = self._rq("POST", f"/wp-json/wp/v2/posts/{post_id}", json=update_data, timeout=30)
        return resp.ok

    def test_connection(self) -> tuple[bool, str]:
        try:
            resp = self._rq("GET", "/wp-json/wp/v2/users/me", timeout=10)
            if resp.ok:
                return True, f"Connected as {resp.json().get('name', 'user')}"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, str(exc)
