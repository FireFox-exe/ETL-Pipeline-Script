# GitHub ETL Pipeline

An automated ETL pipeline built with Python, using the GitHub REST API.

It collects public repository metadata from any GitHub organization (e.g., Netflix, Spotify, Amazon), processes the data into structured `.csv` files, and automatically uploads the results to a GitHub repository — all with a single script run.

The project is modular, fully automated, and API-driven. Built for efficiency, clarity, and reusability.

---

## Notebook as Visual + Logical Blueprint

The included Jupyter Notebook serves as both a logic blueprint and a minimal UI — outlining the structure of the system while using actual functional code. Ideal for step-by-step understanding or testing individual components before full execution.

---

## Features

- **API-powered extraction** of public repo metadata (names, main languages, etc.)
- **Handles dynamic pagination** using per-page limits and looped requests
- **Rate limit aware**: detects API limits via response headers and waits/reacts accordingly
- **Memoization**: caches redundant API calls to avoid waste and speed up process
- **Typed error handling**: distinguishes between network, HTTP, and API-specific failures
- **Infrastructure as code**: creates the destination GitHub repo on the fly if needed
- **DataFrame formatting**: outputs clean `.csv` files ready for SQL or analysis
- **Base64 serialization**: sends files via REST `PUT` requests to GitHub's content API
- **Authentication**: uses token-based access with `.env`-friendly config (secure)
- **Inline docstrings** for every function, following Google-style format
- **Console logs with timestamps**: full visibility at every step
- **Modular design**: easy to reuse, extend, or swap out pieces of the pipeline
- **Zero manual intervention** once configured

---

## Folder Structure

├── data/ - Final .csv output (ready to upload)
├── etl/ - Core ETL logic and API handlers
├── uploader/ - Handles GitHub upload and serialization
├── linguagens_repos.ipynb - Blueprint notebook
├── main.py - One-click entry point
└── .gitignore - Keeps tokens/configs private


---

## Authentication

This project expects a GitHub token stored securely — ideally via `.env` file. You can use `python-dotenv` to load environment variables automatically.

Make sure your script includes:

```python
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
```

---
## Requirements

- Python 3.10+
- `pandas`, `requests`, `tqdm`
- A personal GitHub token (with repo scope)
- Optional: `.env` setup for sensitive variables

---

## Use Case Examples

- Build datasets of tech stacks used by target companies
- Analyze evolution of repository languages across time
- Feed machine learning models with curated GitHub data
- Automate GitHub backup or audit routines

---

## Execution

From `main.py`:

```bash
python main.py
