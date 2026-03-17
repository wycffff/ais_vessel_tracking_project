# Deployment Guide

## Local deployment with Docker

### Step 1

Create the environment file.

```bash
cp .env.example .env
```

### Step 2

Start the services.

```bash
docker compose up --build
```

### Step 3

Initialize the database.

```bash
docker compose exec api python scripts/init_db.py
```

### Step 4

Optional: insert sample data.

```bash
docker compose exec api python scripts/seed_sample_data.py
```

### Step 5

Open the API docs.

```text
http://localhost:8000/docs
```

## Manual deployment without Docker

### Step 1

Install Python dependencies.

```bash
pip install -r requirements.txt
```

### Step 2

Prepare PostgreSQL and `.env`.

### Step 3

Create database tables.

```bash
python scripts/init_db.py
```

### Step 4

Run the API.

```bash
uvicorn app.api.main:app --reload
```

### Step 5

Run ingestion in another terminal.

```bash
python -m app.ingestion.fetch_ais
```

## Simple cloud deployment options

For a student-level final demo, the most practical deployment options are:

- local Docker demo on laptop
- Render or Railway for API hosting
- Neon or Supabase for managed PostgreSQL

For the final course submission, local Docker deployment is usually enough because it is reproducible and easy to demonstrate.
