import streamlit as st
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Admission Events Portal",
    layout="centered"
)

DATA_FILE = "events.csv"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"   # change in production

EVENT_CATEGORIES = [
    "Online Application",
    "Memo Clearance",
    "Option Registration",
    "Provisional Category List",
    "Provisional Rank List",
    "Provisional Allotment",
    "Final Allotment"
]

# --------------------------------------------------
# DATA FUNCTIONS
# --------------------------------------------------
def load_events():
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Start Date", "End Date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "Category",
            "Title",
            "Start Date",
            "End Date"
        ])
    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def remove_expired_events(df):
    today = pd.to_datetime(date.today())
    df = df[df["End Date"] >= today]
    save_events(df)
    return df


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "role" not in st.session_state:
    st.session_state.role = None

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
st.title("📢 Admission Event Notifications")

if st.session_state.role is None:
    role = st.radio("Select Role", ["User", "Admin"])

    if role == "Admin":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login = st.form_submit_button("Login")

            if login:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.role = "Admin"
                    st.success("Admin login successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    else:
        st.session_state.role = "User"
        st.rerun()

# --------------------------------------------------
# LOAD & CLEAN DATA
# --------------------------------------------------
events_df = load_events()
events_df = remove_expired_events(events_df)

# --------------------------------------------------
# ADMIN PANEL
# --------------------------------------------------
if st.session_state.role == "Admin":

    st.subheader("🛠 Admin – Add Event")

    with st.form("add_event", clear_on_submit=True):
        category = st.selectbox("Event Category", EVENT_CATEGORIES)
        title = st.text_input("Event Title / Description")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_value=date.today())
        with col2:
            end_date = st.date_input("End Date", min_value=start_date)

        submit = st.form_submit_button("Add Event")

        if submit:
            if title.strip() == "":
                st.error("Event title is required")
            else:
                new_event = {
                    "Category": category,
                    "Title": title,
                    "Start Date": start_date,
                    "End Date": end_date
                }
                events_df = pd.concat(
                    [events_df, pd.DataFrame([new_event])],
                    ignore_index=True
                )
                save_events(events_df)
                st.success("Event added successfully")

    st.divider()
    st.subheader("📋 Current Events (Admin View)")

    if events_df.empty:
        st.info("No active events")
    else:
        for idx, row in events_df.iterrows():
            with st.container(border=True):
                st.write(f"**Category:** {row['Category']}")
                st.write(f"**Event:** {row['Title']}")
                st.write(f"**Period:** {row['Start Date'].date()} → {row['End Date'].date()}")

                if st.button("❌ Delete", key=f"del_{idx}"):
                    events_df = events_df.drop(idx)
                    save_events(events_df)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.role = None
        st.rerun()

# --------------------------------------------------
# USER VIEW
# --------------------------------------------------
if st.session_state.role == "User":

    st.subheader("📌 Active Admission Events")

    today = pd.to_datetime(date.today())
    active_events = events_df[
        (events_df["Start Date"] <= today) &
        (events_df["End Date"] >= today)
    ]

    if active_events.empty:
        st.info("No active notifications at this time")
    else:
        for _, row in active_events.sort_values("Start Date").iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['Category']}")
                st.write(row["Title"])
                st.write(
                    f"🗓 {row['Start Date'].date()} to {row['End Date'].date()}"
                )

    if st.button("Exit"):
        st.session_state.role = None
        st.rerun()
