import streamlit as st
import pandas as pd
from datetime import date

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Admission Event Notifications",
    layout="centered"
)

DATA_FILE = "events.csv"

# ==================================================
# LOGIN CONFIG
# ==================================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

# ==================================================
# MASTER DATA
# ==================================================
EXAMS = [
    "KEAM",
    "LLB 3 Year",
    "LLB 5 Year",
    "LLM",
    "PG Ayurveda",
    "PG Homoeo",
    "PG Nursing"
]

EVENT_CATEGORIES = [
    "Online Application",
    "Memo Clearance",
    "Option Registration",
    "Provisional Category List",
    "Provisional Rank List",
    "Provisional Allotment",
    "Final Allotment"
]

CATEGORY_PRIORITY = {
    "Final Allotment": 1,
    "Provisional Allotment": 2,
    "Provisional Rank List": 3,
    "Provisional Category List": 4,
    "Option Registration": 5,
    "Memo Clearance": 6,
    "Online Application": 7
}

# ==================================================
# SESSION STATE (SAFE)
# ==================================================
st.session_state.setdefault("page", "login")
st.session_state.setdefault("role", None)

# ==================================================
# DATA FUNCTIONS (HARDENED)
# ==================================================
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(
            columns=["Exam", "Category", "Title", "Start Date", "End Date"]
        )

    # Ensure all required columns exist
    for col in ["Exam", "Category", "Title", "Start Date", "End Date"]:
        if col not in df.columns:
            df[col] = ""

    # Force date parsing (CRITICAL FIX)
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")

    # Drop rows with invalid dates
    df = df.dropna(subset=["Start Date", "End Date"])

    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def event_status(row):
    today = pd.to_datetime(date.today())

    if pd.isna(row["Start Date"]) or pd.isna(row["End Date"]):
        return "Closed"

    if row["End Date"] < today:
        return "Closed"
    elif row["Start Date"] > today:
        return "Upcoming"
    else:
        return "Active"


def status_badge(status):
    return {
        "Active": "🟢 Active",
        "Upcoming": "🟡 Upcoming",
        "Closed": "🔴 Closed"
    }[status]


def enrich_events(df):
    if df.empty:
        return df

    df = df.copy()
    df["Status"] = df.apply(event_status, axis=1)
    df["Priority"] = df["Category"].map(CATEGORY_PRIORITY).fillna(99)
    return df.sort_values(["Exam", "Priority", "Start Date"])


# ==================================================
# LOAD DATA (SAFE)
# ==================================================
events_df = enrich_events(load_events())

# ==================================================
# LOGIN PAGE (GUI)
# ==================================================
if st.session_state.page == "login":

    st.markdown("## 📢 Admission Event Notifications")
    st.markdown("### Please select an option")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Login as Admin", use_container_width=True):
            st.session_state.page = "admin_login"
            st.rerun()

    with col2:
        if st.button("👤 Continue as User", use_container_width=True):
            st.session_state.role = "User"
            st.session_state.page = "user"
            st.rerun()

# ==================================================
# ADMIN LOGIN
# ==================================================
if st.session_state.page == "admin_login":

    st.markdown("## 🔐 Admin Login")

    with st.form("admin_login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")

        if login:
            if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
                st.session_state.role = "Admin"
                st.session_state.page = "admin"
                st.rerun()
            else:
                st.error("Invalid credentials")

    if st.button("⬅ Back"):
        st.session_state.page = "login"
        st.rerun()

# ==================================================
# ADMIN PANEL
# ==================================================
if st.session_state.page == "admin":

    st.markdown("## 🛠 Admin Panel")

    with st.expander("➕ Add New Event", expanded=True):
        with st.form("add_event_form"):
            exam = st.selectbox("Select Exam", EXAMS)
            category = st.selectbox("Event Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")

            c1, c2 = st.columns(2)
            with c1:
                start = st.date_input("Start Date")
            with c2:
                end = st.date_input("End Date", min_value=start)

            if st.form_submit_button("Add Event"):
                if title.strip() == "":
                    st.error("Event description required")
                else:
                    new_row = pd.DataFrame([{
                        "Exam": exam,
                        "Category": category,
                        "Title": title,
                        "Start Date": start,
                        "End Date": end
                    }])
                    save_events(pd.concat([events_df, new_row], ignore_index=True))
                    st.success("Event added")
                    st.rerun()

    st.subheader("📋 All Events")

    if events_df.empty:
        st.info("No events available")
    else:
        for i, row in events_df.reset_index(drop=True).iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['Exam']} – {row['Category']}")
                st.write(row["Title"])
                st.write(f"🗓 {row['Start Date'].date()} → {row['End Date'].date()}")
                st.write(status_badge(row["Status"]))

                if st.button("❌ Delete", key=f"d{i}"):
                    events_df = events_df.drop(i)
                    save_events(events_df)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ==================================================
# USER VIEW
# ==================================================
if st.session_state.page == "user":

    st.markdown("## 📌 Admission Event Schedule")

    selected_exam = st.selectbox("Select Exam", EXAMS)

    visible = events_df[
        (events_df["Exam"] == selected_exam) &
        (events_df["Status"] != "Closed")
    ]

    if visible.empty:
        st.info("No active or upcoming notifications")
    else:
        for _, row in visible.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['Category']}")
                st.write(row["Title"])
                st.write(f"🗓 {row['Start Date'].date()} → {row['End Date'].date()}")
                st.write(status_badge(row["Status"]))

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
