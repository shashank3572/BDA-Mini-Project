import json
import os
import time
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient, ASCENDING

DB_NAME = "library_analytics"

def explain_aggregate(db, pipeline):
    return db.command({
        "explain": {
            "aggregate": "transactions",
            "pipeline": pipeline,
            "cursor": {}
        },
        "verbosity": "executionStats"
    })

def find_execution_stats(node):
    if isinstance(node, dict):
        if "executionStats" in node and isinstance(node["executionStats"], dict):
            stats = node["executionStats"]
            if "totalDocsExamined" in stats or "executionTimeMillis" in stats:
                return stats
        for value in node.values():
            result = find_execution_stats(value)
            if result is not None:
                return result
    elif isinstance(node, list):
        for value in node:
            result = find_execution_stats(value)
            if result is not None:
                return result
    return None

def summarize(label, stats):
    if not stats:
        print(f"{label}: execution stats not found in explain output.")
        return
    print(f"\n{label}")
    print(f"  executionTimeMillis: {stats.get('executionTimeMillis', 'N/A')}")
    print(f"  totalDocsExamined:   {stats.get('totalDocsExamined', 'N/A')}")
    print(f"  totalKeysExamined:   {stats.get('totalKeysExamined', 'N/A')}")
    print(f"  nReturned:           {stats.get('nReturned', 'N/A')}")

def main():
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    if db["transactions"].estimated_document_count() == 0:
        raise SystemExit("No transactions found. Run scripts/generate_data.py first.")

    # Query a recent time window; use a range to make the index relevant.
    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    pipeline = [
        {"$match": {"issueDate": {"$gte": cutoff}}},
        {"$group": {"_id": {"$month": "$issueDate"}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]

    print("Benchmarking an aggregation on recent transactions.")
    existing = [idx["name"] for idx in db["transactions"].list_indexes()]
    had_index = "issueDate_asc" in existing
    if had_index:
        db["transactions"].drop_index("issueDate_asc")

    before = explain_aggregate(db, pipeline)
    summarize("BEFORE index", find_execution_stats(before))

    db["transactions"].create_index([("issueDate", ASCENDING)], name="issueDate_asc")
    after = explain_aggregate(db, pipeline)
    summarize("AFTER index", find_execution_stats(after))

    output = {
        "before": before,
        "after": after,
        "note": "The issueDate_asc index is recreated after the no-index explain. Other indexes remain unchanged. Results depend on dataset size, hardware, cache state, and MongoDB version."
    }
    with open("benchmark_explain.json", "w", encoding="utf-8") as f:
        json.dump(output, f, default=str, indent=2)
    print("\nFull explain output saved to benchmark_explain.json")
    client.close()

if __name__ == "__main__":
    main()
