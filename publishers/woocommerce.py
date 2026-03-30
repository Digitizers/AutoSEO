"""WooCommerce REST API v3 publisher."""
import requests
from requests.auth import HTTPBasicAuth
from publishers.base import BasePlatformPublisher


class WooCommercePublisher(BasePlatformPublisher):
    def _auth(self):
        return HTTPBasicAuth(
            self.config["woocommerce"]["consumer_key"],
            self.config["woocommerce"]["consumer_secret"],
        )

    def _base(self):
        return self.config["woocommerce"]["site_url"].rstrip("/")

    def _fetch_wc_products(self, limit: int = 50) -> list[dict]:
        resp = requests.get(
            f"{self._base()}/wp-json/wc/v3/products",
            auth=self._auth(),
            params={"per_page": min(limit, 100), "status": "publish"},
            timeout=20,
        )
        resp.raise_for_status()
        return [
            {
                "_id": str(p["id"]),
                "title": p.get("name", ""),
                "subtitle": p.get("short_description", ""),
                "image1Url": p.get("images", [{}])[0].get("src", "") if p.get("images") else "",
                "url": p.get("permalink", ""),
                "created_at": p.get("date_created", ""),
                "status": p.get("status", "publish"),
                "price": p.get("price", ""),
            }
            for p in resp.json()
        ]

    def fetch_posts(self, limit: int = 50) -> list[dict]:
        return self._fetch_wc_products(limit)

    def fetch_products(self, limit: int = 50) -> list[dict]:
        return self._fetch_wc_products(limit)

    def publish_post(self, post_data: dict) -> str:
        resp = requests.post(
            f"{self._base()}/wp-json/wc/v3/products",
            auth=self._auth(),
            json=post_data,
            timeout=30,
        )
        resp.raise_for_status()
        return str(resp.json()["id"])

    def update_post(self, post_id: str, update_data: dict) -> bool:
        resp = requests.put(
            f"{self._base()}/wp-json/wc/v3/products/{post_id}",
            auth=self._auth(),
            json=update_data,
            timeout=30,
        )
        return resp.ok

    def upload_image(self, image_bytes: bytes, filename: str = "image.jpg") -> str | None:
        """Upload to WP media library if wp_username + wp_app_password are set in config.
        WooCommerce runs on WordPress, so the WP REST API is available at the same site_url.
        Add 'wp_username' and 'wp_app_password' to your woocommerce config block to enable this.
        """
        wc = self.config["woocommerce"]
        wp_user = wc.get("wp_username", "")
        wp_pass = wc.get("wp_app_password") or wc.get("wp_password", "")
        if not wp_user or not wp_pass:
            return None
        try:
            resp = requests.post(
                f"{self._base()}/wp-json/wp/v2/media",
                auth=(wp_user, wp_pass),
                headers={
                    "Content-Type": "image/jpeg",
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
                data=image_bytes,
                timeout=60,
            )
            if resp.ok:
                return resp.json().get("source_url")
            print(f"  [wc] Media upload failed: HTTP {resp.status_code}")
        except Exception as exc:
            print(f"  [wc] Media upload error: {exc}")
        return None

    def test_connection(self) -> tuple[bool, str]:
        try:
            resp = requests.get(
                f"{self._base()}/wp-json/wc/v3/system_status",
                auth=self._auth(),
                timeout=10,
            )
            if resp.ok:
                return True, "WooCommerce connected"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            return False, str(e)
