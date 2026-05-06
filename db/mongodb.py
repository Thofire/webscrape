from pymongo import MongoClient
from datetime import datetime, timezone
import os

def get_collection():
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["price_tracker"]
    return db["prices"]

def upload_to_mongo(collection, all_data):
    for site, url, name, price in all_data:
        collection.insert_one({
            "site": site,
            "url": url,
            "name": name,
            "price": price,
            "timestamp": datetime.now(timezone.utc)
        })
    print("✅ Done! Data saved to MongoDB.")