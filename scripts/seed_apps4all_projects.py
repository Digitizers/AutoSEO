"""
Seed apps4all projects into MongoDB.
Run from the seo-blog-engine directory:
    python scripts/seed_apps4all_projects.py
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import yaml
from pymongo import MongoClient

CONFIG_PATH = Path(__file__).parent.parent / "config.apps4all.yaml"
DATA_PATH = Path(__file__).parent.parent.parent.parent / "apps4all" / "scripts" / "apps_data.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    mongo_uri = config["mongodb"]["uri"]
    database = config["mongodb"]["database"]
    collection_name = config["mongodb"]["collection"]

    if not DATA_PATH.exists():
        print(f"[error] Data file not found: {DATA_PATH}")
        print("  Run from apps4all directory: node -e \"import('./lib/apps.js').then(m => process.stdout.write(JSON.stringify(m.appsData)))\" > scripts/apps_data.json")
        sys.exit(1)

    with open(DATA_PATH, encoding="utf-8") as f:
        apps_data = json.load(f)

    print(f"Loaded {len(apps_data)} projects from apps_data.json")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
    try:
        db = client[database]
        col = db[collection_name]

        # Idempotency check
        existing = col.count_documents({"type": "project"})
        if existing > 0:
            print(f"Already seeded — {existing} project(s) in collection. Skipping.")
            return

        docs = []
        for i, app in enumerate(apps_data):
            docs.append({
                **app,
                "type": "project",
                "order": i,
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            })

        result = col.insert_many(docs)
        print(f"✓ Seeded {len(result.inserted_ids)} projects into {database}/{collection_name}")

        sample = col.find_one({"type": "project"})
        print(f"  Sample: \"{sample.get('headline', '?')}\" (slug: {sample.get('slug', '?')})")

    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
