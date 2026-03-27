import streamlit as st
import pandas as pd

# ------------------------
# PAGE CONFIG
# ------------------------
st.set_page_config(page_title="Reconciliation Dashboard", layout="wide")

st.title("Payment Reconciliation Dashboard")
st.markdown("Identify mismatches between transactions and settlements.")

# ------------------------
# LOAD DATA
# ------------------------
@st.cache_data
def load_data():
    transactions = pd.read_csv("data/transactions.csv")
    settlements = pd.read_csv("data/settlements.csv")

    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"])
    settlements["settlement_date"] = pd.to_datetime(settlements["settlement_date"])

    transactions["amount"] = transactions["amount"].astype(float)
    settlements["amount"] = settlements["amount"].astype(float)

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
# DETECT GAPS
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
# UI - SUMMARY
# ------------------------
st.subheader("Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Transactions", f"{total_txn:,.2f}")
col2.metric("Total Settlements", f"{total_settle:,.2f}")
col3.metric("Difference", f"{difference:,.2f}")

# ------------------------
# ISSUE BREAKDOWN
# ------------------------
st.subheader("Issue Breakdown")

col1, col2 = st.columns(2)

with col1:
    st.write("### Count")
    st.bar_chart(issue_counts)

with col2:
    st.write("### Percentage")
    issue_percent = (issue_counts / issue_counts.sum()) * 100
    st.dataframe(issue_percent.round(2).astype(str) + " %")

# ------------------------
# FILTER SECTION
# ------------------------
st.subheader("Filter Issues")

issue_filter = st.selectbox(
    "Select Issue Type",
    ["All"] + sorted(result["issue_type"].unique())
)

if issue_filter == "All":
    filtered = result
else:
    filtered = result[result["issue_type"] == issue_filter]

# ------------------------
# DATA TABLE
# ------------------------
st.subheader("Detailed Records")
st.dataframe(filtered, use_container_width=True)

# ------------------------
# PROBLEMATIC RECORDS
# ------------------------
st.subheader("Problematic Records Only")

issues_only = result[result["issue_type"] != "Matched"]
st.dataframe(issues_only, use_container_width=True)

# ------------------------
# INSIGHTS
# ------------------------
st.subheader("Key Insights")

st.write(f"Total Problematic Records: {len(issues_only)}")

top_issue = issue_counts.idxmax()
st.write(f"Most Frequent Issue: **{top_issue}**")

if "amount_txn" in issues_only.columns:
    impact = issues_only.groupby("issue_type")["amount_txn"].sum().abs()
    top_impact = impact.idxmax()
    st.write(f"Highest Financial Impact: **{top_impact}**")

st.markdown("---")
