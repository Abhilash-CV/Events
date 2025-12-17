import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Event Test", layout="centered")

DATA_FILE = "events.csv"

# -------------------------------
# LOAD / SAVE
# -------------------------------
def load_events():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(
            columns=["EventID", "Exam", "Category", "Title", "Start Date", "End Date"]
        )


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


# -------------------------------
# UI
# -------------------------------
st.title("🧪 Event Add Test (Multiple Rows)")

df = load_events()

st.info(f"📄 Total rows in CSV: {len(df)}")

with st.form("add_form"):
    exam = st.selectbox("Exam", ["KEAM", "LLB", "PG Nursing"])
    category = st.selectbox("Category", ["Online Application", "Final Allotment"])
    title = st.text_input("Event Title")
    start = st.date_input("Start Date", value=date.today())
    end = st.date_input("End Date", value=date.today())
    submit = st.form_submit_button("Add Event")

if submit:
    new_id = 1 if df.empty else int(df["EventID"].max()) + 1

    new_row = {
        "EventID": new_id,
        "Exam": exam,
        "Category": category,
        "Title": title,
        "Start Date": start,
        "End Date": end
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_events(df)

    st.success(f"Event {new_id} added")
    st.rerun()

st.divider()
st.subheader("📋 Raw CSV Contents (NO FILTERING)")

st.dataframe(df, use_container_width=True)
