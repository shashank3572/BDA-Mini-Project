import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics import (
    top_books_pipeline,
    monthly_trend_pipeline,
    genre_pipeline,
    overdue_by_department_pipeline,
    overdue_rate_pipeline,
)

DB_NAME = "library_analytics"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

st.set_page_config(page_title="Library Usage Analytics", page_icon="📚", layout="wide")
st.title("📚 Library Usage Analytics")
st.caption("Big Data Analytics mini project | VTU BCS714D | Synthetic demonstration data")

@st.cache_resource
def get_database():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    return client[DB_NAME]

try:
    db = get_database()
    tx = db["transactions"]
    books = db["books"]
    members = db["members"]
    tx_count = tx.estimated_document_count()
    book_count = books.estimated_document_count()
    member_count = members.estimated_document_count()

    summary = list(tx.aggregate(overdue_rate_pipeline()))
    metrics = summary[0] if summary else {
        "total": 0, "overdue": 0, "overdueRatePct": 0, "totalFines": 0
    }

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{tx_count:,}")
    c2.metric("Books", f"{book_count:,}")
    c3.metric("Members", f"{member_count:,}")
    c4.metric("Overdue rate", f"{metrics.get('overdueRatePct', 0):.2f}%")
    st.caption(f"Total recorded fines in generated data: ₹{metrics.get('totalFines', 0):,.2f}")

    st.subheader("Borrowing trends")
    monthly = list(tx.aggregate(monthly_trend_pipeline()))
    if monthly:
        df_monthly = pd.DataFrame(monthly)
        st.plotly_chart(
            px.line(df_monthly, x="month", y="borrowCount", markers=True,
                    title="Transactions by month", labels={"month": "Month", "borrowCount": "Borrowings"}),
            use_container_width=True
        )
    else:
        st.info("No transactions available yet. Run the data generator first.")

    left, right = st.columns(2)
    with left:
        st.subheader("Most borrowed books")
        top = list(tx.aggregate(top_books_pipeline(10)))
        if top:
            df_top = pd.DataFrame(top)
            st.plotly_chart(
                px.bar(df_top.sort_values("borrowCount"), x="borrowCount", y="title",
                       color="genre", orientation="h",
                       labels={"borrowCount": "Borrow count", "title": "Book"}),
                use_container_width=True
            )
        else:
            st.info("No book borrowing data found.")

    with right:
        st.subheader("Borrowing by genre")
        genres = list(tx.aggregate(genre_pipeline()))
        if genres:
            df_genre = pd.DataFrame(genres)
            st.plotly_chart(
                px.pie(df_genre, names="genre", values="borrowCount", hole=0.35),
                use_container_width=True
            )
        else:
            st.info("No genre data found.")

    st.subheader("Overdue transactions by department")
    overdue = list(tx.aggregate(overdue_by_department_pipeline()))
    if overdue:
        df_overdue = pd.DataFrame(overdue)
        st.plotly_chart(
            px.bar(df_overdue, x="department", y="overdueCount", color="department",
                   hover_data=["totalFines"],
                   labels={"overdueCount": "Overdue transactions", "department": "Department"}),
            use_container_width=True
        )
        st.dataframe(df_overdue, use_container_width=True, hide_index=True)
    else:
        st.info("No overdue transactions found.")

    with st.expander("Database and collection details"):
        st.write("Database: `library_analytics`")
        st.write("Collections: `books`, `members`, `transactions`")
        st.write("MongoDB connection: local URI by default; override with `MONGODB_URI`.")
        st.write("All data is synthetic and generated for academic demonstration.")
except PyMongoError as exc:
    st.error("Cannot connect to MongoDB. Start the local MongoDB service, then refresh this page.")
    st.code(str(exc))
    st.markdown("Setup guide: [MongoDB Community Server on Windows](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/)")
