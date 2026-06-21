# Zerayakob-student-record

## Kail Academy Student Performance Analysis System

This project provides a Streamlit app that:
- uploads multiple CSV student data files
- uploads multiple teacher-report PDFs
- merges and cleans CSV data
- computes scores, attendance, subject performance, ranking, and weak/strong students
- extracts rule-based PDF insights (positive/negative/behavior/improvement notes)
- combines CSV + PDF results into rule-based student insights
- generates and downloads a PDF report

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown by Streamlit in your browser.
