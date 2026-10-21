# Library Usage Analytics using MongoDB

A Big Data Analytics mini project for VTU BCS714D. The project uses synthetic library data to analyze borrowing patterns, overdue returns, genre popularity, and monthly trends.

## Architecture

Synthetic data generator -> MongoDB collections -> aggregation pipelines -> Streamlit + Plotly dashboard

Collections:
- `books`: title, author, genre, publication year, total copies
- `members`: member details and department
- `transactions`: book/member references, issue/due/return dates, fine, status

## Prerequisites

- Python 3.10+
- MongoDB Community Server running locally on `mongodb://localhost:27017`
- Optional: MongoDB Compass for visually inspecting the database

Official setup references:
- MongoDB Community Server for Windows: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/
- Streamlit installation: https://docs.streamlit.io/get-started/installation
- PyMongo aggregation guide: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/

## Windows setup

Open PowerShell in this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\\Scripts\\activate.bat
```

Make sure MongoDB is running. If installed as a Windows service, open Services and start the `MongoDB` service.

## Step 1: Generate and load data

Start with 100,000 transactions to validate the pipeline:

```powershell
python scripts/generate_data.py --transactions 100000 --batch-size 5000
```

To scale up after the first successful run:

```powershell
python scripts/generate_data.py --transactions 500000 --batch-size 5000
```

For a clean rebuild, the script clears only this project's three collections (`books`, `members`, and `transactions`) in the `library_analytics` database before loading. Do not point it at a database containing unrelated data.

The default connection is `mongodb://localhost:27017`. Override with `MONGODB_URI` if required.

## Step 2: Create indexes

```powershell
python scripts/setup_indexes.py
```

## Step 3: Launch dashboard

```powershell
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Step 4: Benchmark query execution

```powershell
python scripts/benchmark.py
```

The script reports execution statistics before and after creating an index on `issueDate`. Save the actual output for the report. Results vary by laptop, dataset size, cache state, and MongoDB version.

## Analytics included

1. Top borrowed books
2. Borrowing trend by month
3. Borrowing distribution by genre
4. Overdue transactions by department
5. Summary KPIs
6. Index performance comparison using MongoDB explain statistics

## Suggested demo flow

1. Show the three collections in MongoDB Compass.
2. Explain why transactions reference `bookId` and `memberId`.
3. Run the generator and show document counts.
4. Run the dashboard and explain each chart.
5. Run the benchmark and discuss the actual execution statistics.

## Important academic note

All data is synthetic and for demonstration only. Do not describe synthetic data as real library data. Do not invent performance improvements; report the measured results from your own run.
