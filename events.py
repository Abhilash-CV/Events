import streamlit as st
import pandas as pd
from datetime import date, time

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Admission Events", layout="wide")

DATA_FILE = "events.csv"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

PROGRAMS = [
    "KEAM", "LLB 3 Year", "LLB 5 Year", "LLM",
    "PG Ayurveda", "PG Homoeo", "PG Nursing"
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

CATEGORY_COLORS = {
    "Online Application": "#ff6f61",
    "Memo Clearance": "#f4b400",
    "Option Registration": "#4285f4",
    "Provisional Category List": "#9c27b0",
    "Provisional Rank List": "#00acc1",
    "Provisional Allotment": "#43a047",
    "Final Allotment": "#e53935"
}

BASE_COLUMNS = [
    "EventID", "Program", "Category", "Title",
    "Start Date", "End Date", "Start Time", "End Time"
]

# --------------------------------------------------
# SESSION
# --------------------------------------------------
st.session_state.setdefault("page", "user")
st.session_state.setdefault("edit_id", None)

# --------------------------------------------------
# DATA
# --------------------------------------------------
def load_events():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=BASE_COLUMNS)


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def next_event_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


# --------------------------------------------------
# STATUS
# --------------------------------------------------
def event_status(row):
    today = pd.Timestamp.today().normalize()
    start = pd.to_datetime(row["Start Date"])
    end = pd.to_datetime(row["End Date"])

    if end < today:
        return "Closed"
    elif start > today:
        return "Upcoming"
    return "Active"


# --------------------------------------------------
# STYLES
# --------------------------------------------------
st.markdown("""
<style>
.event-card {
    background:white;
    border-radius:18px;
    padding:20px;
    text-align:center;
    box-shadow:0 8px 20px rgba(0,0,0,.08);
    transition:.25s;
    margin-bottom:24px;
}
.event-card:hover {
    transform:translateY(-6px);
    box-shadow:0 16px 32px rgba(0,0,0,.15);
}
.today { border:3px solid black; }
.month-header {
    font-size:26px;
    font-weight:800;
    margin:30px 0 20px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CARD
# --------------------------------------------------
def render_event_card(row):
    start = pd.to_datetime(row["Start Date"])
    month = start.strftime("%b").upper()
    day = start.strftime("%d")
    today_cls = "today" if start.date() == date.today() else ""
    color = CATEGORY_COLORS.get(row["Category"], "#333")

    st.markdown(f"""
    <div class="event-card {today_cls}">
        <div style="color:{color}; font-weight:700">{month}</div>
        <div style="font-size:42px; font-weight:800">{day}</div>
        <div style="font-size:13px;color:#666">
            {row["Start Time"]} – {row["End Time"]}
        </div>
        <div style="margin-top:10px;font-weight:600">{row["Title"]}</div>
        <div style="font-size:12px;color:#888">{row["Program"]}</div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------
if st.session_state.page == "admin_login":

    st.subheader("🔐 Admin Login")

    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")

    if ok and u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
        st.session_state.page = "admin"
        st.rerun()
    elif ok:
        st.error("Invalid credentials")

    if st.button("⬅ Back"):
        st.session_state.page = "user"
        st.rerun()

# --------------------------------------------------
# ADMIN PANEL
# --------------------------------------------------
elif st.session_state.page == "admin":

    st.subheader("🛠 Admin Panel")

    with st.expander("➕ Add Event", expanded=True):
        with st.form("add"):
            program = st.selectbox("Program", PROGRAMS)
            category = st.selectbox("Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")

            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start Date")
            end_date = c2.date_input("End Date", min_value=start_date)

            t1, t2 = st.columns(2)
            start_time = t1.time_input("Start Time", time(10, 0))
            end_time = t2.time_input("End Time", time(17, 0))

            add = st.form_submit_button("Add Event")

        if add and title.strip():
            df = load_events()
            df = pd.concat([df, pd.DataFrame([{
                "EventID": next_event_id(df),
                "Program": program,
                "Category": category,
                "Title": title,
                "Start Date": start_date,
                "End Date": end_date,
                "Start Time": start_time.strftime("%I:%M %p"),
                "End Time": end_time.strftime("%I:%M %p")
            }])], ignore_index=True)
            save_events(df)
            st.rerun()

    if st.button("Logout"):
        st.session_state.page = "user"
        st.rerun()

# --------------------------------------------------
# USER LANDING PAGE (DEFAULT)
# --------------------------------------------------
else:

    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔐 Admin Login"):
            st.session_state.page = "admin_login"
            st.rerun()

    st.markdown("## 📅 Upcoming Events")

    program = st.selectbox(
        "Filter by Program",
        ["All Programs"] + PROGRAMS
    )

    df = load_events()

    if df.empty:
        st.info("No events available")
    else:
        df["Start Date"] = pd.to_datetime(df["Start Date"])
        df["End Date"] = pd.to_datetime(df["End Date"])
        df["Status"] = df.apply(event_status, axis=1)

        df = df[df["Status"] != "Closed"]

        if program != "All Programs":
            df = df[df["Program"] == program]

        df = df.sort_values("Start Date")
        df["Month"] = df["Start Date"].dt.strftime("%B")

        for month, grp in df.groupby("Month"):
            st.markdown(f"<div class='month-header'>{month}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, row) in enumerate(grp.iterrows()):
                with cols[i % 3]:
                    render_event_card(row)
