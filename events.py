import streamlit as st
import pandas as pd
from datetime import date

# ==================================================
# CONFIG
# ==================================================
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
    "Online Application": "#ff7675",
    "Memo Clearance": "#6c5ce7",
    "Option Registration": "#00b894",
    "Provisional Category List": "#0984e3",
    "Provisional Rank List": "#e84393",
    "Provisional Allotment": "#fdcb6e",
    "Final Allotment": "#d63031"
}

# ==================================================
# SESSION STATE
# ==================================================
st.session_state.setdefault("page", "login")
st.session_state.setdefault("edit_id", None)

# ==================================================
# DATA FUNCTIONS
# ==================================================
def load_events():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(
            columns=["EventID", "Exam", "Category", "Title", "Start Date", "End Date"]
        )


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def next_event_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


# ==================================================
# STATUS
# ==================================================
def event_status(row):
    today = pd.Timestamp.today().normalize()
    start = pd.to_datetime(row["Start Date"])
    end = pd.to_datetime(row["End Date"])

    if start.date() == date.today():
        return "Today"
    if end < today:
        return "Closed"
    if start > today:
        return "Upcoming"
    return "Active"


# ==================================================
# GLOBAL STYLES
# ==================================================
st.markdown("""
<style>
.event-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 22px;
}
.event-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 28px rgba(0,0,0,0.15);
}
.month-header {
    font-size: 26px;
    font-weight: 800;
    margin: 30px 0 10px 0;
    border-bottom: 3px solid #ddd;
    padding-bottom: 6px;
}
.today-badge {
    background: #00b894;
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    display: inline-block;
    margin-bottom: 8px;
}
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# LOGIN PAGE
# ==================================================
if st.session_state.page == "login":

    st.title("📢 Admission Event Notifications")

    c1, c2 = st.columns(2)
    if c1.button("🔐 Login as Admin", use_container_width=True):
        st.session_state.page = "admin_login"
        st.rerun()

    if c2.button("👤 Continue as User", use_container_width=True):
        st.session_state.page = "user"
        st.rerun()

# ==================================================
# ADMIN LOGIN
# ==================================================
elif st.session_state.page == "admin_login":

    st.subheader("🔐 Admin Login")

    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ok = st.form_submit_button("Login")

    if ok:
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
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
elif st.session_state.page == "admin":

    st.subheader("🛠 Admin Panel")

    with st.expander("➕ Add Event", expanded=True):
        with st.form("add_event"):
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
            st.success("Event added")
            st.rerun()

    st.divider()
    st.subheader("📋 Manage Events")

    df = load_events()
    if df.empty:
        st.info("No events")
    else:
        for _, r in df.iterrows():
            with st.expander(f"{r['Exam']} – {r['Category']} (ID {r['EventID']})", expanded=False):
                st.write(r["Title"])
                st.write(f"{r['Start Date']} → {r['End Date']}")

                c1, c2 = st.columns(2)
                if c1.button("✏️ Edit", key=f"ed{r['EventID']}"):
                    st.session_state.edit_id = r["EventID"]
                    st.session_state.page = "edit"
                    st.rerun()
                if c2.button("❌ Delete", key=f"dl{r['EventID']}"):
                    save_events(df[df["EventID"] != r["EventID"]])
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ==================================================
# USER VIEW (POSTER STYLE)
# ==================================================
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
            df["Month"] = df["Start Date"].dt.strftime("%B %Y")

            for month, group in df.groupby("Month"):
                st.markdown(f"<div class='month-header'>{month}</div>", unsafe_allow_html=True)

                cols = st.columns(3)
                for i, (_, r) in enumerate(group.iterrows()):
                    with cols[i % 3]:
                        color = CATEGORY_COLORS.get(r["Category"], "#333")
                        day = r["Start Date"].strftime("%d")
                        month_short = r["Start Date"].strftime("%b").upper()
                        time = f"{r['Start Date'].strftime('%H:%M')} – {r['End Date'].strftime('%H:%M')}"

                        badge = ""
                        if r["Status"] == "Today":
                            badge = "<div class='today-badge'>TODAY</div>"

                        st.markdown(
                            f"""
                            <div class="event-card" style="border-top:6px solid {color}">
                                {badge}
                                <div style="font-size:14px;font-weight:700;color:{color}">
                                    {month_short}
                                </div>
                                <div style="font-size:42px;font-weight:800">
                                    {day}
                                </div>
                                <div style="font-size:13px;color:#555">
                                    {time}
                                </div>
                                <div style="margin-top:10px;font-size:15px;font-weight:600">
                                    {r['Title']}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
