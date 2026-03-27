import streamlit as st
import pandas as pd

st.set_page_config(page_title="Reconciliation Dashboard", layout="wide")

st.title("Payment Reconciliation Dashboard")

# ------------------------
# LOAD DATA
# ------------------------
@st.cache_data
def load_data():
    transactions = pd.read_csv("data/transactions.csv")
    settlements = pd.read_csv("data/settlements.csv")

    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
    settlements["settlement_date"] = pd.to_datetime(settlements["settlement_date"])

    return transactions, settlements

transactions, settlements = load_data()

# ------------------------
# MATCH
# ------------------------
merged = transactions.merge(
    settlements,
    on="transaction_id",
    how="outer",
    suffixes=("_txn", "_settle")
)

# ------------------------
# DETECT
# ------------------------
def detect_gaps(df):
    issue_types = []
    explanations = []

    for _, row in df.iterrows():

        if pd.isna(row["amount_settle"]):
            issue_types.append("Missing Settlement")
            explanations.append("Transaction recorded but no settlement found")

        elif pd.isna(row["amount_txn"]):
            issue_types.append("Missing Transaction")
            explanations.append("Settlement exists without original transaction")

        elif abs(row["amount_txn"] - row["amount_settle"]) > 0.01:
            issue_types.append("Amount Mismatch")
            explanations.append("Mismatch in transaction and settlement amount")

        elif row["transaction_date"].month != row["settlement_date"].month:
            issue_types.append("Timing Issue")
            explanations.append("Settlement occurred in a different month")

        else:
            issue_types.append("Matched")
            explanations.append("Transaction matches settlement")

    df["issue_type"] = issue_types
    df["explanation"] = explanations
    return df

result = detect_gaps(merged)

# ------------------------
# SUMMARY
# ------------------------
total_txn = transactions["amount"].sum()
total_settle = settlements["amount"].sum()
difference = total_txn - total_settle

issue_counts = result["issue_type"].value_counts()

# ------------------------
# UI
# ------------------------
st.subheader("Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Total Transactions", f"{total_txn:.2f}")
col2.metric("Total Settlements", f"{total_settle:.2f}")
col3.metric("Difference", f"{difference:.2f}")

st.subheader("Issue Breakdown")
st.bar_chart(issue_counts)

st.subheader("Filter Issues")

issue_filter = st.selectbox(
    "Select Issue Type",
    ["All"] + list(result["issue_type"].unique())
)

if issue_filter == "All":
    filtered = result
else:
    filtered = result[result["issue_type"] == issue_filter]

st.dataframe(filtered)