import streamlit as st
import pandas as pd
from datetime import date

# ==================================================
# APP CONFIG
# ==================================================
st.set_page_config(page_title="Admission Events", layout="centered")

DATA_FILE = "events.csv"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

# ==================================================
# MASTER DATA
# ==================================================
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
st.session_state.setdefault("edit_event_id", None)

# ==================================================
# DATA LAYER (SOURCE OF TRUTH)
# ==================================================
BASE_COLUMNS = [
    "EventID", "Order", "Exam", "Category",
    "Title", "Start Date", "End Date"
]

def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=BASE_COLUMNS)

    # Ensure schema
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Force types
    df["EventID"] = pd.to_numeric(df["EventID"], errors="coerce")
    df["Order"] = pd.to_numeric(df["Order"], errors="coerce")
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")

    # Drop corrupt rows
    df = df.dropna(subset=["EventID", "Order", "Start Date", "End Date"])

    return df.sort_values("Order").reset_index(drop=True)


def save_events(df):
    df[BASE_COLUMNS].to_csv(DATA_FILE, index=False)


def next_event_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


def next_order(df):
    return 1 if df.empty else int(df["Order"].max()) + 1


# ==================================================
# RUNTIME (DERIVED) LOGIC
# ==================================================
def event_status(row):
    today = pd.to_datetime(date.today())
    if row["End Date"] < today:
        return "Closed"
    elif row["Start Date"] > today:
        return "Upcoming"
    return "Active"


def enrich(df):
    if df.empty:
        return df

    df = df.copy()
    df["Status"] = df.apply(event_status, axis=1)
    df["CatPriority"] = df["Category"].map(CATEGORY_PRIORITY).fillna(99)
    return df.sort_values(["Exam", "CatPriority", "Order"])


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
                st.error("Event description is required")
            else:
                df = load_events()
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame([{
                            "EventID": next_event_id(df),
                            "Order": next_order(df),
                            "Exam": exam,
                            "Category": category,
                            "Title": title,
                            "Start Date": start,
                            "End Date": end
                        }])
                    ],
                    ignore_index=True
                )
                save_events(df)
                st.success("Event added successfully")
                st.rerun()

    # ---------- MANAGE EVENTS ----------
    base_df = load_events()
    view_df = enrich(base_df)

    st.divider()
    st.subheader("📋 Manage Events")

    if view_df.empty:
        st.info("No events available")
    else:
        for _, r in view_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### {r['Exam']} – {r['Category']}")
                st.write(r["Title"])
                st.write(f"{r['Start Date'].date()} → {r['End Date'].date()} ({r['Status']})")

                c1, c2, c3, c4 = st.columns(4)

                # Move Up
                if c1.button("⬆", key=f"up{r['EventID']}"):
                    df = load_events()
                    idx = df.index[df["EventID"] == r["EventID"]][0]
                    if idx > 0:
                        df.loc[idx, "Order"], df.loc[idx - 1, "Order"] = (
                            df.loc[idx - 1, "Order"],
                            df.loc[idx, "Order"]
                        )
                        save_events(df)
                        st.rerun()

                # Move Down
                if c2.button("⬇", key=f"dn{r['EventID']}"):
                    df = load_events()
                    idx = df.index[df["EventID"] == r["EventID"]][0]
                    if idx < len(df) - 1:
                        df.loc[idx, "Order"], df.loc[idx + 1, "Order"] = (
                            df.loc[idx + 1, "Order"],
                            df.loc[idx, "Order"]
                        )
                        save_events(df)
                        st.rerun()

                # Edit
                if c3.button("✏️ Edit", key=f"ed{r['EventID']}"):
                    st.session_state.edit_event_id = r["EventID"]
                    st.session_state.page = "edit"
                    st.rerun()

                # Delete
                if c4.button("❌ Delete", key=f"dl{r['EventID']}"):
                    df = load_events()
                    df = df[df["EventID"] != r["EventID"]]
                    save_events(df)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()


# ==================================================
# EDIT EVENT
# ==================================================
elif st.session_state.page == "edit":

    df = load_events()
    event = df[df["EventID"] == st.session_state.edit_event_id].iloc[0]

    st.subheader("✏️ Edit Event")

    with st.form("edit_form"):
        exam = st.selectbox("Exam", EXAMS, index=EXAMS.index(event["Exam"]))
        category = st.selectbox("Category", EVENT_CATEGORIES,
                                index=EVENT_CATEGORIES.index(event["Category"]))
        title = st.text_input("Description", value=event["Title"])

        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date", value=event["Start Date"])
        end = c2.date_input("End Date", value=event["End Date"], min_value=start)

        update = st.form_submit_button("Update Event")

    if update:
        df.loc[df["EventID"] == event["EventID"],
               ["Exam", "Category", "Title", "Start Date", "End Date"]] = \
            [exam, category, title, start, end]

        save_events(df)
        st.session_state.page = "admin"
        st.success("Event updated")
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
