from datetime import datetime, timedelta, timezone

def top_books_pipeline(limit=10):
    return [
        {"$group": {"_id": "$bookId", "borrowCount": {"$sum": 1}}},
        {"$sort": {"borrowCount": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "books",
            "localField": "_id",
            "foreignField": "_id",
            "as": "book"
        }},
        {"$unwind": {"path": "$book", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "title": {"$ifNull": ["$book.title", "Unknown book"]},
            "genre": {"$ifNull": ["$book.genre", "Unknown"]},
            "borrowCount": 1
        }}
    ]

def monthly_trend_pipeline():
    return [
        {
            "$match": {
                "$expr": {
                    "$lt": [
                        "$issueDate",
                        {
                            "$dateTrunc": {
                                "date": "$$NOW",
                                "unit": "month"
                            }
                        }
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$issueDate"},
                    "month": {"$month": "$issueDate"}
                },
                "borrowCount": {"$sum": 1}
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {
            "$project": {
                "_id": 0,
                "month": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month",
                                "day": 1
                            }
                        }
                    }
                },
                "borrowCount": 1
            }
        }
    ]

def genre_pipeline():
    return [
        {"$lookup": {
            "from": "books",
            "localField": "bookId",
            "foreignField": "_id",
            "as": "book"
        }},
        {"$unwind": "$book"},
        {"$group": {
            "_id": "$book.genre",
            "borrowCount": {"$sum": 1}
        }},
        {"$sort": {"borrowCount": -1}},
        {"$project": {"_id": 0, "genre": "$_id", "borrowCount": 1}}
    ]

def overdue_by_department_pipeline():
    return [
        {"$match": {"status": "overdue"}},
        {"$lookup": {
            "from": "members",
            "localField": "memberId",
            "foreignField": "_id",
            "as": "member"
        }},
        {"$unwind": "$member"},
        {"$group": {
            "_id": "$member.department",
            "overdueCount": {"$sum": 1},
            "totalFines": {"$sum": "$fineAmount"}
        }},
        {"$sort": {"overdueCount": -1}},
        {"$project": {
            "_id": 0,
            "department": "$_id",
            "overdueCount": 1,
            "totalFines": {"$round": ["$totalFines", 2]}
        }}
    ]

def overdue_rate_pipeline():
    return [
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "overdue": {"$sum": {"$cond": [{"$eq": ["$status", "overdue"]}, 1, 0]}},
            "fines": {"$sum": "$fineAmount"}
        }},
        {"$project": {
            "_id": 0,
            "total": 1,
            "overdue": 1,
            "overdueRatePct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$overdue", "$total"]}, 100]},
                    2
                ]
            },
            "totalFines": {"$round": ["$fines", 2]}
        }}
    ]
