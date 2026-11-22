# DataFlow Studio

A small, public-facing Streamlit portfolio demo for data cleaning and quick analysis.

## Features
- Upload CSV and Excel files
- Preview data and inspect missing values / data types / unique values
- Remove duplicate rows
- Handle missing values
- Trim whitespace in text columns
- Remove selected columns
- View a numeric distribution chart and summary statistics
- Export cleaned data to CSV or Excel

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push `app.py`` and `requirements.txt` to a GitHub repository, then create an app on Streamlit Community Cloud and select the repository, branch, and `app.py`.

## Privacy note
This demo processes uploaded files during the active app session. Do not upload confidential, personal, or sensitive data to a public demo.
