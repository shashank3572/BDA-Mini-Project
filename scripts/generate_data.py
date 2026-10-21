import argparse
import os
import random
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

DB_NAME = "library_analytics"
DEPARTMENTS = ["CSE", "CSE-AIML", "ISE", "ECE", "EEE", "ME", "CV", "MBA"]
GENRES = ["Computer Science", "AI & Machine Learning", "Fiction", "History",
          "Science", "Mathematics", "Business", "Biography", "Cybersecurity"]
FIRST_NAMES = ["Aarav", "Aditi", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya",
               "Kiran", "Meera", "Nikhil", "Priya", "Rahul", "Riya", "Rohan",
               "Sahana", "Shrey", "Tanvi", "Varun", "Vikram", "Zoya"]
LAST_NAMES = ["Sharma", "Rao", "Patel", "Kumar", "Shetty", "Reddy", "Nair",
              "Iyer", "Gupta", "Joshi", "Das", "Verma", "Bhat", "Singh"]
TITLES = [
    "Python Programming", "Database Systems", "Introduction to AI",
    "Machine Learning Essentials", "Data Structures in Practice",
    "The Silent Library", "A Brief History of Science", "Statistics for Students",
    "Cybersecurity Fundamentals", "Big Data Analytics", "Deep Learning Basics",
    "The Art of Problem Solving", "Cloud Computing Concepts",
    "Computer Networks", "Applied Mathematics", "Business Intelligence",
    "Computer Vision in Action", "Modern Operating Systems",
    "Natural Language Processing", "The Curious Researcher"
]

def random_name(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

def batched_insert(collection, docs, batch_size):
    for start in range(0, len(docs), batch_size):
        collection.insert_many(docs[start:start + batch_size], ordered=False)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic library analytics data.")
    parser.add_argument("--transactions", type=int, default=100000)
    parser.add_argument("--members", type=int, default=1000)
    parser.add_argument("--books", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.transactions < 1 or args.members < 1 or args.books < 1 or args.batch_size < 1:
        parser.error("All counts and batch-size must be positive integers.")

    rng = random.Random(args.seed)
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except PyMongoError as exc:
        raise SystemExit(
            "Could not connect to MongoDB. Start the local MongoDB service and try again.\n"
            f"Connection detail: {exc}"
        )

    db = client[DB_NAME]
    books_col, members_col, tx_col = db["books"], db["members"], db["transactions"]

    print(f"Connected. Clearing {DB_NAME}.books, members, and transactions...")
    books_col.delete_many({})
    members_col.delete_many({})
    tx_col.delete_many({})

    books = []
    for i in range(args.books):
        title = TITLES[i % len(TITLES)]
        suffix = f" Vol. {i // len(TITLES) + 1}" if i >= len(TITLES) else ""
        books.append({
            "title": title + suffix,
            "author": random_name(rng),
            "genre": rng.choice(GENRES),
            "isbn": f"978-{rng.randrange(1000000000, 9999999999)}",
            "publishedYear": rng.randint(1995, 2025),
            "copies": rng.randint(1, 12),
            "tags": rng.sample(["popular", "reference", "course", "new", "classic", "research"], k=2)
        })
    books_col.insert_many(books)
    book_ids = [doc["_id"] for doc in books_col.find({}, {"_id": 1})]

    members = []
    for i in range(args.members):
        joined = datetime(2021, 1, 1, tzinfo=timezone.utc) + timedelta(days=rng.randint(0, 1700))
        members.append({
            "name": random_name(rng),
            "memberCode": f"LIB{i + 1:06d}",
            "department": rng.choice(DEPARTMENTS),
            "year": rng.randint(1, 4),
            "joinedAt": joined,
            "membershipType": rng.choice(["Student", "Faculty", "Researcher"])
        })
    members_col.insert_many(members)
    member_ids = [doc["_id"] for doc in members_col.find({}, {"_id": 1})]

    # A fixed historical window makes the generated trend reproducible.
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=730)
    days = (end - start).days
    print(f"Generating {args.transactions:,} transactions in batches of {args.batch_size:,}...")
    inserted = 0
    while inserted < args.transactions:
        n = min(args.batch_size, args.transactions - inserted)
        docs = []
        for _ in range(n):
            issue = start + timedelta(
                days=rng.randrange(max(days, 1)),
                hours=rng.randrange(8, 21),
                minutes=rng.randrange(60)
            )
            due = issue + timedelta(days=14)
            status_roll = rng.random()
            if status_roll < 0.70:
                return_date = issue + timedelta(days=rng.randint(1, 14))
                status = "returned"
                fine = 0.0
            elif status_roll < 0.84:
                return_date = None
                status = "overdue" if due < end else "issued"
                fine = min(
                        100.0,
                        round(max(0, (end.date() - due.date()).days) * 2.0, 2)
                ) if status == "overdue" else 0.0
            else:
                return_date = issue + timedelta(days=rng.randint(15, 40))
                status = "returned_late"
                late_days = max(1, (return_date.date() - due.date()).days)
                fine = min(100.0, round(late_days * 2.0, 2))
            docs.append({
                "memberId": rng.choice(member_ids),
                "bookId": rng.choice(book_ids),
                "issueDate": issue,
                "dueDate": due,
                "returnDate": return_date,
                "fineAmount": fine,
                "status": status
            })
        tx_col.insert_many(docs, ordered=False)
        inserted += n
        print(f"Inserted {inserted:,}/{args.transactions:,}")

    print("\nData generation complete.")
    print(f"books: {books_col.count_documents({}):,}")
    print(f"members: {members_col.count_documents({}):,}")
    print(f"transactions: {tx_col.count_documents({}):,}")
    print("Next: python scripts/setup_indexes.py")
    client.close()

if __name__ == "__main__":
    main()
