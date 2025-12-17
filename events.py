import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Events Admin", layout="centered")

DATA_FILE = "events.csv"

# --------------------------------------------------
# DATA LAYER (NO MAGIC)
# --------------------------------------------------
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(
            columns=["EventID", "Exam", "Category", "Title", "Start Date", "End Date"]
        )

    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("📋 Events Admin – HARD RESET VERSION")

df = load_events()

st.info(f"📄 Total events in CSV: {len(df)}")

# ---------------- ADD EVENT ----------------
with st.form("add_event_form"):
    exam = st.selectbox("Exam", ["KEAM", "LLB 3 Year", "PG Nursing"])
    category = st.selectbox(
        "Category",
        ["Online Application", "Provisional Rank List", "Final Allotment"]
    )
    title = st.text_input("Event Description")
    start = st.date_input("Start Date", value=date.today())
    end = st.date_input("End Date", value=date.today())

    add = st.form_submit_button("Add Event")

if add:
    if title.strip() == "":
        st.error("Description required")
    else:
        df = load_events()

        new_id = 1 if df.empty else int(df["EventID"].max()) + 1

        new_row = pd.DataFrame([{
            "EventID": new_id,
            "Exam": exam,
            "Category": category,
            "Title": title,
            "Start Date": start,
            "End Date": end
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        save_events(df)

        st.success(f"Event {new_id} added")
        st.rerun()

st.divider()

# ---------------- MANAGE EVENTS ----------------
st.subheader("📋 Manage Events (RAW VIEW – NO FILTERING)")

df = load_events()

if df.empty:
    st.warning("No events found")
else:
    # THIS TABLE WILL ALWAYS SHOW ALL ROWS
    st.dataframe(df, use_container_width=True)

    st.divider()

    for _, r in df.iterrows():
        with st.container(border=True):
            st.markdown(f"**EventID {r['EventID']}**")
            st.write(f"Exam: {r['Exam']}")
            st.write(f"Category: {r['Category']}")
            st.write(r["Title"])
            st.write(f"{r['Start Date']} → {r['End Date']}")

            if st.button("❌ Delete", key=f"del_{r['EventID']}"):
                df = df[df["EventID"] != r["EventID"]]
                save_events(df)
                st.rerun()
