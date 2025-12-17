import streamlit as st
import pandas as pd
from datetime import date

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Admission Event Notifications",
    layout="centered"
)

DATA_FILE = "events.csv"

# --------------------------------------------------
# LOGIN CONFIG
# --------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

# --------------------------------------------------
# EVENT CONFIG
# --------------------------------------------------
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

# --------------------------------------------------
# DATA FUNCTIONS
# --------------------------------------------------
def load_events():
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Start Date", "End Date"])
    except FileNotFoundError:
        df = pd.DataFrame(
            columns=["Category", "Title", "Start Date", "End Date"]
        )
    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def get_status(row):
    today = pd.to_datetime(date.today())
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
    """Always rebuild derived columns safely"""
    if df.empty:
        return df

    df = df.copy()
    df["Status"] = df.apply(get_status, axis=1)
    df["Priority"] = df["Category"].map(CATEGORY_PRIORITY)
    return df.sort_values(["Priority", "Start Date"])


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "role" not in st.session_state:
    st.session_state.role = None

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
st.title("📢 Admission Event Notifications")

if st.session_state.role is None:
    role = st.radio("Login As", ["User", "Admin"])

    if role == "Admin":
        with st.form("admin_login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

            if login:
                if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
                    st.session_state.role = "Admin"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        st.session_state.role = "User"
        st.rerun()

# --------------------------------------------------
# LOAD & ENRICH DATA
# --------------------------------------------------
events_df = load_events()
events_df = enrich_events(events_df)

# ==================================================
# ADMIN VIEW
# ==================================================
if st.session_state.role == "Admin":

    st.subheader("🛠 Admin Panel")

    # ---------------- ADD EVENT ----------------
    with st.expander("➕ Add New Event", expanded=True):
        with st.form("add_event"):
            cat = st.selectbox("Event Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")
            c1, c2 = st.columns(2)
            with c1:
                start = st.date_input("Start Date", min_value=date.today())
            with c2:
                end = st.date_input("End Date", min_value=start)

            if st.form_submit_button("Add Event"):
                if title.strip() == "":
                    st.error("Event description required")
                else:
                    new_row = pd.DataFrame([{
                        "Category": cat,
                        "Title": title,
                        "Start Date": start,
                        "End Date": end
                    }])
                    save_events(pd.concat([events_df, new_row], ignore_index=True))
                    st.success("Event added successfully")
                    st.rerun()

    # ---------------- MANAGE EVENTS ----------------
    st.subheader("📋 All Events")

    if events_df.empty:
        st.info("No events available")
    else:
        events_df = events_df.reset_index(drop=True)

        for i, row in events_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['Category']}")
                st.write(row["Title"])
                st.write(
                    f"🗓 {row['Start Date'].date()} → {row['End Date'].date()}"
                )
                st.write(status_badge(row["Status"]))

                if st.button("❌ Delete", key=f"del_{i}"):
                    events_df = events_df.drop(i)
                    save_events(events_df)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.role = None
        st.rerun()

# ==================================================
# USER VIEW
# ==================================================
if st.session_state.role == "User":

    st.subheader("📌 Admission Event Schedule")

    if events_df.empty:
        st.info("No notifications available")
    else:
        visible = events_df[events_df["Status"] != "Closed"]

        if visible.empty:
            st.info("No active or upcoming notifications")
        else:
            for _, row in visible.iterrows():
                with st.container(border=True):
                    st.markdown(f"### {row['Category']}")
                    st.write(row["Title"])
                    st.write(
                        f"🗓 {row['Start Date'].date()} → {row['End Date'].date()}"
                    )
                    st.write(status_badge(row["Status"]))

    if st.button("Exit"):
        st.session_state.role = None
        st.rerun()
