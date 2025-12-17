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
# DATA FUNCTIONS
# ==================================================
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(
            columns=[
                "EventID", "Exam", "Category", "Title",
                "Start Date", "End Date", "Order"
            ]
        )

    if df.empty:
        return df

    if "EventID" not in df.columns:
        df.insert(0, "EventID", range(1, len(df) + 1))

    if "Order" not in df.columns:
        df["Order"] = range(1, len(df) + 1)

    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.dropna(subset=["Start Date", "End Date"])

    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def event_status(row):
    today = pd.to_datetime(date.today())
    if row["End Date"] < today:
        return "Closed"
    elif row["Start Date"] > today:
        return "Upcoming"
    else:
        return "Active"


def enrich(df):
    if df.empty:
        return df

    df = df.copy()
    df["Status"] = df.apply(event_status, axis=1)
    df["CatPriority"] = df["Category"].map(CATEGORY_PRIORITY).fillna(99)

    return df.sort_values(
        ["Exam", "CatPriority", "Order"]
    )


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

    # -------- ADD EVENT --------
    with st.expander("➕ Add Event", expanded=True):
        with st.form("add_event"):
            exam = st.selectbox("Exam", EXAMS)
            category = st.selectbox("Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")

            c1, c2 = st.columns(2)
            start = c1.date_input("Start Date")
            end = c2.date_input("End Date", min_value=start)

            submit = st.form_submit_button("Add Event")

        if submit and title.strip():
            df = load_events()
            new_id = 1 if df.empty else df["EventID"].max() + 1
            new_order = 1 if df.empty else df["Order"].max() + 1

            new_row = {
                "EventID": new_id,
                "Exam": exam,
                "Category": category,
                "Title": title,
                "Start Date": start,
                "End Date": end,
                "Order": new_order
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_events(df)
            st.success("Event added")
            st.rerun()

    # -------- MANAGE EVENTS --------
    df = enrich(load_events())

    st.divider()
    st.subheader("📋 Manage Events")

    if df.empty:
        st.info("No events available")
    else:
        for _, r in df.iterrows():
            with st.container(border=True):
                st.markdown(f"### {r['Exam']} – {r['Category']}")
                st.write(r["Title"])
                st.write(f"{r['Start Date'].date()} → {r['End Date'].date()} ({r['Status']})")

                col1, col2, col3, col4 = st.columns(4)

                # ---- MOVE UP ----
                if col1.button("⬆ Move Up", key=f"up{r['EventID']}"):
                    base = load_events()
                    idx = base.index[base["EventID"] == r["EventID"]][0]
                    if idx > 0:
                        base.loc[idx, "Order"], base.loc[idx - 1, "Order"] = (
                            base.loc[idx - 1, "Order"],
                            base.loc[idx, "Order"]
                        )
                        save_events(base)
                        st.rerun()

                # ---- MOVE DOWN ----
                if col2.button("⬇ Move Down", key=f"dn{r['EventID']}"):
                    base = load_events()
                    idx = base.index[base["EventID"] == r["EventID"]][0]
                    if idx < len(base) - 1:
                        base.loc[idx, "Order"], base.loc[idx + 1, "Order"] = (
                            base.loc[idx + 1, "Order"],
                            base.loc[idx, "Order"]
                        )
                        save_events(base)
                        st.rerun()

                # ---- EDIT ----
                if col3.button("✏️ Edit", key=f"ed{r['EventID']}"):
                    st.session_state.edit_id = r["EventID"]
                    st.session_state.page = "edit"
                    st.rerun()

                # ---- DELETE ----
                if col4.button("❌ Delete", key=f"dl{r['EventID']}"):
                    base = load_events()
                    base = base[base["EventID"] != r["EventID"]]
                    save_events(base)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ==================================================
# EDIT EVENT PAGE
# ==================================================
elif st.session_state.page == "edit":

    df = load_events()
    event = df[df["EventID"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ Edit Event")

    with st.form("edit_form"):
        exam = st.selectbox("Exam", EXAMS, index=EXAMS.index(event["Exam"]))
        category = st.selectbox("Category", EVENT_CATEGORIES, index=EVENT_CATEGORIES.index(event["Category"]))
        title = st.text_input("Description", value=event["Title"])

        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date", value=event["Start Date"])
        end = c2.date_input("End Date", value=event["End Date"], min_value=start)

        update = st.form_submit_button("Update")

    if update:
        df.loc[df["EventID"] == event["EventID"], ["Exam", "Category", "Title", "Start Date", "End Date"]] = [
            exam, category, title, start, end
        ]
        save_events(df)
        st.success("Event updated")
        st.session_state.page = "admin"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "admin"
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
                st.markdown(f"### {r['Category']}")
                st.write(r["Title"])
                st.write(f"{r['Start Date'].date()} → {r['End Date'].date()} ({r['Status']})")

    if st.button("Exit"):
        st.session_state.clear()
        st.rerun()
