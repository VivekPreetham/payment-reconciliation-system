# Payment Reconciliation System

## Problem
A payments platform records transactions instantly, but bank settlements occur later. At month end, both should match — but they don’t.

## Solution
This project builds a reconciliation system that:
- Matches transactions with settlements
- Detects mismatches
- Classifies issues
- Provides explanations

## Features
- Missing Settlement detection
- Missing Transaction detection
- Amount mismatch detection
- Timing issue detection
- Interactive dashboard

## Tech Stack
- Python
- Pandas
- Streamlit

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py