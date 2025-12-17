import streamlit as st
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
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

BASE_COLUMNS = [
    "EventID", "Exam", "Category", "Title", "Start Date", "End Date"
]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
st.session_state.setdefault("page", "login")
st.session_state.setdefault("edit_id", None)

# --------------------------------------------------
# DATA FUNCTIONS (STABLE)
# --------------------------------------------------
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=BASE_COLUMNS)
    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def next_event_id(df):
    if df.empty:
        return 1
    return int(df["EventID"].max()) + 1


# --------------------------------------------------
# STATUS (USER VIEW ONLY)
# --------------------------------------------------
def event_status(row):
    today = date.today()
    if row["End Date"] < today:
        return "Closed"
    elif row["Start Date"] > today:
        return "Upcoming"
    else:
        return "Active"


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

# --------------------------------------------------
# ADMIN PANEL
# --------------------------------------------------
elif st.session_state.page == "admin":

    st.subheader("🛠 Admin Panel")

    # ---------- ADD EVENT ----------
    with st.expander("➕ Add Event", expanded=True):
        with st.form("add_event_form"):
            exam = st.selectbox("Exam", EXAMS)
            category = st.selectbox("Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")

            c1, c2 = st.columns(2)
            start = c1.date_input("Start Date")
            end = c2.date_input("End Date", min_value=start)

            add = st.form_submit_button("Add Event")

        if add:
            if not title.strip():
                st.error("Event description required")
            else:
                df = load_events()
                new_row = {
                    "EventID": next_event_id(df),
                    "Exam": exam,
                    "Category": category,
                    "Title": title,
                    "Start Date": start,
                    "End Date": end
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_events(df)
                st.success("Event added successfully")
                st.rerun()

    # ---------- MANAGE EVENTS ----------
    st.divider()
    st.subheader("📋 Manage Events")

    df = load_events()

    if df.empty:
        st.info("No events available")
    else:
        for _, r in df.iterrows():
            with st.expander(
                f"{r['Exam']} – {r['Category']} (Event ID {r['EventID']})",
                expanded=True
            ):
                st.write(r["Title"])
                st.write(f"{r['Start Date']} → {r['End Date']}")

                c1, c2 = st.columns(2)

                if c1.button("✏️ Edit", key=f"ed_{r['EventID']}"):
                    st.session_state.edit_id = r["EventID"]
                    st.session_state.page = "edit"
                    st.rerun()

                if c2.button("❌ Delete", key=f"dl_{r['EventID']}"):
                    df2 = df[df["EventID"] != r["EventID"]]
                    save_events(df2)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --------------------------------------------------
# EDIT EVENT
# --------------------------------------------------
elif st.session_state.page == "edit":

    df = load_events()
    e = df[df["EventID"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ Edit Event")

    with st.form("edit_form"):
        exam = st.selectbox("Exam", EXAMS, index=EXAMS.index(e["Exam"]))
        category = st.selectbox(
            "Category",
            EVENT_CATEGORIES,
            index=EVENT_CATEGORIES.index(e["Category"])
        )
        title = st.text_input("Description", value=e["Title"])

        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date", value=pd.to_datetime(e["Start Date"]))
        end = c2.date_input("End Date", value=pd.to_datetime(e["End Date"]))

        update = st.form_submit_button("Update")

    if update:
        df.loc[df["EventID"] == e["EventID"],
               ["Exam", "Category", "Title", "Start Date", "End Date"]] = \
            [exam, category, title, start, end]
        save_events(df)
        st.session_state.page = "admin"
        st.success("Event updated")
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "admin"
        st.rerun()

# --------------------------------------------------
# USER VIEW
# --------------------------------------------------
elif st.session_state.page == "user":

    st.subheader("📌 Admission Event Schedule")

    exam = st.selectbox("Select Exam", EXAMS)
    df = load_events()

    if df.empty:
        st.info("No events available")
    else:
        df["Start Date"] = pd.to_datetime(df["Start Date"])
        df["End Date"] = pd.to_datetime(df["End Date"])
        df["Status"] = df.apply(event_status, axis=1)

        df = df[(df["Exam"] == exam) & (df["Status"] != "Closed")]

        if df.empty:
            st.info("No active or upcoming events")
        else:
            for _, r in df.iterrows():
                badge = "🟢 Active" if r["Status"] == "Active" else "🟡 Upcoming"
                with st.container(border=True):
                    st.markdown(f"### {r['Category']} {badge}")
                    st.write(r["Title"])
                    st.write(f"{r['Start Date']} → {r['End Date']}")

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
