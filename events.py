import streamlit as st
import pandas as pd
from datetime import date

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Admission Events", layout="centered")

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
# SESSION STATE
# ==================================================
st.session_state.setdefault("page", "login")

# ==================================================
# DATA HELPERS
# ==================================================
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Exam", "Category", "Title", "Start Date", "End Date"])

    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.dropna(subset=["Start Date", "End Date"])
    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def enrich(df):
    today = pd.to_datetime(date.today())
    df = df.copy()
    df["Status"] = df.apply(
        lambda r: "Closed" if r["End Date"] < today
        else "Upcoming" if r["Start Date"] > today
        else "Active",
        axis=1
    )
    df["Priority"] = df["Category"].map(CATEGORY_PRIORITY).fillna(99)
    return df.sort_values(["Exam", "Priority", "Start Date"])


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

    with st.form("login_form"):
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

    # -------- ADD EVENT (THIS WORKS) --------
    with st.form("add_event"):
        exam = st.selectbox("Exam", EXAMS)
        category = st.selectbox("Category", EVENT_CATEGORIES)
        title = st.text_input("Event Description")

        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date")
        end = c2.date_input("End Date", min_value=start)

        submit = st.form_submit_button("Add Event")

    if submit:
        if title.strip() == "":
            st.error("Description required")
        else:
            df = load_events()   # 🔑 RELOAD CLEAN DATA
            df = pd.concat([df, pd.DataFrame([{
                "Exam": exam,
                "Category": category,
                "Title": title,
                "Start Date": start,
                "End Date": end
            }])], ignore_index=True)
            save_events(df)
            st.success("Event added successfully")
            st.rerun()

    # -------- LIST EVENTS --------
    df = enrich(load_events())

    st.divider()
    st.subheader("📋 Existing Events")

    if df.empty:
        st.info("No events found")
    else:
        for i, r in df.reset_index(drop=True).iterrows():
            with st.container(border=True):
                st.write(f"**{r['Exam']} – {r['Category']}**")
                st.write(r["Title"])
                st.write(f"{r['Start Date'].date()} → {r['End Date'].date()} ({r['Status']})")

                if st.button("❌ Delete", key=f"d{i}"):
                    base = load_events().drop(i)
                    save_events(base)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()


# ==================================================
# USER VIEW
# ==================================================
elif st.session_state.page == "user":

    st.subheader("📌 Admission Event Schedule")

    exam = st.selectbox("Select Exam", EXAMS)
    df = enrich(load_events())

    df = df[(df["Exam"] == exam) & (df["Status"] != "Closed")]

    if df.empty:
        st.info("No active or upcoming events")
    else:
        for _, r in df.iterrows():
            with st.container(border=True):
                st.write(f"**{r['Category']}**")
                st.write(r["Title"])
                st.write(f"{r['Start Date'].date()} → {r['End Date'].date()} ({r['Status']})")

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
