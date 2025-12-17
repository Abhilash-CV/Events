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

# ==================================================
# SESSION STATE
# ==================================================
st.session_state.setdefault("page", "login")
st.session_state.setdefault("edit_id", None)

# ==================================================
# DATA LAYER (STABLE)
# ==================================================
BASE_COLS = ["EventID", "Order", "Exam", "Category", "Title", "Start Date", "End Date"]

def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=BASE_COLS)

    for c in BASE_COLS:
        if c not in df.columns:
            df[c] = None

    df["EventID"] = pd.to_numeric(df["EventID"], errors="coerce")
    df["Order"] = pd.to_numeric(df["Order"], errors="coerce")
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")

    df = df.dropna(subset=["EventID", "Order", "Start Date", "End Date"])
    return df.sort_values("Order").reset_index(drop=True)


def save_events(df):
    df[BASE_COLS].to_csv(DATA_FILE, index=False)


def next_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


def next_order(df):
    return 1 if df.empty else int(df["Order"].max()) + 1


# ==================================================
# DERIVED LOGIC
# ==================================================
def event_status(row):
    today = pd.to_datetime(date.today())
    if row["End Date"] < today:
        return "Closed"
    if row["Start Date"] > today:
        return "Upcoming"
    return "Active"


def enrich(df):
    if df.empty:
        return df
    df = df.copy()
    df["Status"] = df.apply(event_status, axis=1)
    return df


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
            df = pd.concat(
                [df, pd.DataFrame([{
                    "EventID": next_id(df),
                    "Order": next_order(df),
                    "Exam": exam,
                    "Category": category,
                    "Title": title,
                    "Start Date": start,
                    "End Date": end
                }])],
                ignore_index=True
            )
            save_events(df)
            st.success("Event added")
            st.rerun()

    # ---------- MANAGE EVENTS ----------
    # ---------- MANAGE EVENTS ----------
view_df = load_events()

st.divider()
st.subheader("📋 Manage Events")

if view_df.empty:
    st.info("No events available")
else:
    for i, r in view_df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {r['Exam']} – {r['Category']}")
            st.write(r["Title"])
            st.write(
                f"{r['Start Date'].date()} → {r['End Date'].date()}"
            )

            c1, c2, c3, c4 = st.columns(4)

            # Move Up
            if c1.button("⬆", key=f"up{r['EventID']}"):
                df = load_events()
                idx = df.index[df["EventID"] == r["EventID"]][0]
                if idx > 0:
                    df.loc[idx, "Order"], df.loc[idx-1, "Order"] = \
                        df.loc[idx-1, "Order"], df.loc[idx, "Order"]
                    save_events(df)
                    st.rerun()

            # Move Down
            if c2.button("⬇", key=f"dn{r['EventID']}"):
                df = load_events()
                idx = df.index[df["EventID"] == r["EventID"]][0]
                if idx < len(df)-1:
                    df.loc[idx, "Order"], df.loc[idx+1, "Order"] = \
                        df.loc[idx+1, "Order"], df.loc[idx, "Order"]
                    save_events(df)
                    st.rerun()

            # Edit
            if c3.button("✏️ Edit", key=f"ed{r['EventID']}"):
                st.session_state.edit_id = r["EventID"]
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
    e = df[df["EventID"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ Edit Event")

    with st.form("edit_form"):
        exam = st.selectbox("Exam", EXAMS, index=EXAMS.index(e["Exam"]))
        category = st.selectbox("Category", EVENT_CATEGORIES, index=EVENT_CATEGORIES.index(e["Category"]))
        title = st.text_input("Description", value=e["Title"])

        c1, c2 = st.columns(2)
        start = c1.date_input("Start Date", value=e["Start Date"])
        end = c2.date_input("End Date", value=e["End Date"], min_value=start)

        update = st.form_submit_button("Update Event")

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
