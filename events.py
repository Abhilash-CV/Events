import streamlit as st
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Admission Events", layout="wide")

DATA_FILE = "events.csv"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

EXAMS = [
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
    "EventID", "Exam", "Category", "Title", "Start Date", "End Date"
]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
st.session_state.setdefault("page", "login")
st.session_state.setdefault("edit_id", None)

# --------------------------------------------------
# DATA FUNCTIONS
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
# GLOBAL STYLES (POSTER FEEL)
# --------------------------------------------------
st.markdown("""
<style>
.event-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 24px;
}
.event-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 14px 28px rgba(0,0,0,0.15);
}
.today {
    border: 3px solid #000;
}
.month-header {
    font-size: 26px;
    font-weight: 800;
    margin: 30px 0 20px;
}
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# EVENT CARD
# --------------------------------------------------
def render_event_card(event):
    start = pd.to_datetime(event["Start Date"])
    end = pd.to_datetime(event["End Date"])

    is_today = start.date() == date.today()
    month = start.strftime("%b").upper()
    day = start.strftime("%d")
    time = f"{start.strftime('%I:%M %p')} – {end.strftime('%I:%M %p')}"
    title = event["Title"]
    color = CATEGORY_COLORS.get(event["Category"], "#333")

    cls = "event-card today" if is_today else "event-card"

    st.markdown(
        f"""
        <div class="{cls}">
            <div style="color:{color}; font-weight:700;">{month}</div>
            <div style="font-size:44px; font-weight:800;">{day}</div>
            <div style="font-size:13px; color:#666;">{time}</div>
            <div style="margin-top:10px; font-weight:600;">{title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
if st.session_state.page == "login":

    st.title("📢 Admission Event Notifications")

    c1, c2 = st.columns(2)
    if c1.button("🔐 Login as Admin", use_container_width=True):
        st.session_state.page = "admin_login"
        st.rerun()

    if c2.button("👤 Continue as User", use_container_width=True):
        st.session_state.page = "user"
        st.rerun()

# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------
elif st.session_state.page == "admin_login":

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
        st.session_state.page = "login"
        st.rerun()

# --------------------------------------------------
# ADMIN PANEL (UNCHANGED CORE)
# --------------------------------------------------
elif st.session_state.page == "admin":

    st.subheader("🛠 Admin Panel")

    with st.expander("➕ Add Event", expanded=True):
        with st.form("add"):
            exam = st.selectbox("Exam", EXAMS)
            category = st.selectbox("Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")
            c1, c2 = st.columns(2)
            start = c1.date_input("Start Date")
            end = c2.date_input("End Date", min_value=start)
            add = st.form_submit_button("Add Event")

        if add and title.strip():
            df = load_events()
            df = pd.concat([df, pd.DataFrame([{
                "EventID": next_event_id(df),
                "Exam": exam,
                "Category": category,
                "Title": title,
                "Start Date": start,
                "End Date": end
            }])], ignore_index=True)
            save_events(df)
            st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --------------------------------------------------
# USER VIEW (FULL FEATURED)
# --------------------------------------------------
elif st.session_state.page == "user":

    st.markdown("## 📅 Upcoming Events")

    exam = st.selectbox("Select Exam", EXAMS)

    df = load_events()

    if df.empty:
        st.info("No events available")
    else:
        df["Start Date"] = pd.to_datetime(df["Start Date"])
        df["End Date"] = pd.to_datetime(df["End Date"])
        df["Status"] = df.apply(event_status, axis=1)

        df = df[(df["Exam"] == exam) & (df["Status"] != "Closed")]
        df = df.sort_values("Start Date")

        if df.empty:
            st.info("No upcoming events")
        else:
            df["Month"] = df["Start Date"].dt.strftime("%B")

            for month, group in df.groupby("Month"):
                st.markdown(f"<div class='month-header'>{month}</div>", unsafe_allow_html=True)

                cols = st.columns(3)
                for i, (_, row) in enumerate(group.iterrows()):
                    with cols[i % 3]:
                        render_event_card(row)

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
