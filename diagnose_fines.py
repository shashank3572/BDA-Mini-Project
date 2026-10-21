from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["library_analytics"]
transactions = db["transactions"]

print("Database:", db.name)
print("Transaction count:", transactions.count_documents({}))
print("Documents with fine field:", transactions.count_documents({"fine": {"$exists": True}}))
print("Documents with positive fine:", transactions.count_documents({"fine": {"$gt": 0}}))

print("\nSample transaction:")
print(transactions.find_one({}, {"_id": 0}))

print("\nCollections:", db.list_collection_names())

client.close()
