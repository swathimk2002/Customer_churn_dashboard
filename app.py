# import basic libraries
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import warnings
import sqlite3
from sklearn.linear_model import LinearRegression

# hide warnings and set dark theme for charts
warnings.filterwarnings('ignore')
plt.style.use('dark_background')

# page settings
st.set_page_config(page_title="Churn Dashboard", layout="wide")

# title
st.title("Customer Churn Dashboard")

# load dataset
df = pd.read_csv("Telco_Customer_Churn.csv")

# clean data (convert TotalCharges to number)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
df.dropna(inplace=True)

# convert churn Yes/No to 1/0
df['Churn'] = df['Churn'].map({'Yes':1, 'No':0})

# -----------------------------
# sidebar filters
# -----------------------------
st.sidebar.header("Filter Options")

gender = st.sidebar.selectbox("Select Gender", df['gender'].unique())
contract = st.sidebar.selectbox("Select Contract", df['Contract'].unique())

# filter data
filtered_df = df[
    (df['gender'] == gender) &
    (df['Contract'] == contract)
].copy()

# -----------------------------
# key metrics
# -----------------------------
st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", len(filtered_df))
col2.metric("Churn Rate", f"{filtered_df['Churn'].mean()*100:.2f}%")
col3.metric("Avg Charges", f"{filtered_df['MonthlyCharges'].mean():.2f}")

# show data
st.subheader("Dataset Preview")
st.write(filtered_df.head())

# -----------------------------
# charts
# -----------------------------

# bar chart (filtered data)
st.subheader("Filtered Data: Monthly Charges vs Churn")

fig, ax = plt.subplots(figsize=(4,2))
filtered_df.groupby('Churn')['MonthlyCharges'].mean().plot(
    kind='bar', ax=ax, color=['#00ADB5', '#FF2E63']
)
st.pyplot(fig)


# full dataset chart
st.subheader("Overall Data: Monthly Charges vs Churn")

fig, ax = plt.subplots(figsize=(4,2))
df.groupby('Churn')['MonthlyCharges'].mean().plot(kind='bar', ax=ax)
st.pyplot(fig)

# pie chart
st.subheader("Churn Distribution")

fig2, ax2 = plt.subplots(figsize=(4,2))
filtered_df['Churn'].value_counts().plot(
    kind='pie',
    autopct='%1.1f%%',
    ax=ax2,
    colors=['#00ADB5', '#FF2E63']
)
ax2.set_ylabel("")
st.pyplot(fig2)

# tenure vs churn
st.subheader("Tenure vs Churn")

fig3, ax3 = plt.subplots(figsize=(4,2))
filtered_df.groupby('Churn')['tenure'].mean().plot(kind='bar', ax=ax3)
st.pyplot(fig3)

# -----------------------------
# risk score (simple logic)
# -----------------------------

# create risk score
filtered_df['Risk_Score'] = (
    (filtered_df['MonthlyCharges'] * 0.4) +
    ((1 / (filtered_df['tenure'] + 1)) * 50)
)

# label high / low risk
filtered_df['Risk_Level'] = filtered_df['Risk_Score'].apply(
    lambda x: 'High' if x > 30 else 'Low'
)

# show high risk customers
st.subheader("High Risk Customers")

st.write(
    filtered_df[filtered_df['Risk_Level'] == 'High']
    [['customerID', 'MonthlyCharges', 'tenure', 'Risk_Score']]
    .head()
)

# -----------------------------
# SQL part
# -----------------------------

st.subheader("SQL Analysis")

# create temporary database
conn = sqlite3.connect(':memory:')
df.to_sql('churn_data', conn, index=False, if_exists='replace')

# query 1
st.write("Customer Count by Churn")

query1 = """
SELECT Churn, COUNT(*) as Total_Customers
FROM churn_data
GROUP BY Churn
"""
st.write(pd.read_sql(query1, conn))

# query 2
st.write("Avg Monthly Charges by Contract")

query2 = """
SELECT Contract, AVG(MonthlyCharges) as Avg_Charges
FROM churn_data
GROUP BY Contract
"""
st.write(pd.read_sql(query2, conn))

# -----------------------------
# Linear Regression
# -----------------------------

st.subheader("Linear Regression (Simple ML)")

# input (X) and output (y)
X = filtered_df[['tenure']]
y = filtered_df['MonthlyCharges']

# create and train model
model = LinearRegression()
model.fit(X, y)

# predict values
y_pred = model.predict(X)

# plot graph
fig4, ax4 = plt.subplots(figsize=(4,2))

ax4.scatter(X, y, alpha=0.3)   # actual data
ax4.plot(X, y_pred, linewidth=2)  # prediction line

ax4.set_title("Tenure vs Monthly Charges")
ax4.set_xlabel("Tenure")
ax4.set_ylabel("Monthly Charges")

st.pyplot(fig4)

# show equation
st.write("Model Equation:")
st.write(f"y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}")