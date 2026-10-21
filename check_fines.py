from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["library_analytics"]
transactions = db["transactions"]

print("Total transactions:", transactions.count_documents({}))
print("Overdue:", transactions.count_documents({"status": "overdue"}))
print("Returned late:", transactions.count_documents({"status": "returned_late"}))

pipeline = [
    {
        "$group": {
            "_id": None,
            "totalFines": {"$sum": "$fineAmount"}
        }
    }
]

result = list(transactions.aggregate(pipeline))

print("Total fines:", result[0]["totalFines"] if result else 0)

client.close()