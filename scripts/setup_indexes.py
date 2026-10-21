import os
from pymongo import MongoClient, ASCENDING, DESCENDING

DB_NAME = "library_analytics"

def main():
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[DB_NAME]
    db["transactions"].create_index([("issueDate", ASCENDING)], name="issueDate_asc")
    db["transactions"].create_index([("status", ASCENDING)], name="status_asc")
    db["transactions"].create_index([("memberId", ASCENDING), ("issueDate", DESCENDING)], name="member_issueDate")
    db["transactions"].create_index([("bookId", ASCENDING), ("issueDate", DESCENDING)], name="book_issueDate")
    db["members"].create_index([("department", ASCENDING)], name="department_asc")
    db["books"].create_index([("genre", ASCENDING)], name="genre_asc")
    print("Indexes created:")
    for coll_name in ["transactions", "members", "books"]:
        print(f"\n{coll_name}")
        for index in db[coll_name].list_indexes():
            print(f"  {index['name']}: {index['key']}")
    client.close()

if __name__ == "__main__":
    main()
