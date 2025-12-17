import streamlit as st
import pandas as pd
from datetime import date, time

# ==================================================
# CONFIG
# ==================================================
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

BASE_COLUMNS = [
    "EventID", "Program", "Category", "Title",
    "Start Date", "End Date",
    "Start Time", "End Time", "All Day"
]

# ==================================================
# SESSION
# ==================================================
st.session_state.setdefault("page", "user")
st.session_state.setdefault("edit_id", None)

# ==================================================
# DATA (BACKWARD SAFE)
# ==================================================
def load_events():
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=BASE_COLUMNS)

    for c in BASE_COLUMNS:
        if c not in df.columns:
            df[c] = ""

    return df


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def next_event_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


# ==================================================
# STATUS (SAFE)
# ==================================================
def event_status(row):
    today = pd.Timestamp.today().normalize()
    start = row["Start Date"]
    end = row["End Date"]

    if end < today:
        return "Closed"
    elif start > today:
        return "Upcoming"
    return "Active"

# ==================================================
# STYLES (VERY COMPACT CARDS)
# ==================================================
st.markdown("""
<style>
.event-card {
    background:#ffffff;
    border-radius:8px;
    padding:8px 6px;
    text-align:center;
    box-shadow:0 1px 6px rgba(0,0,0,.08);
    margin-bottom:10px;
}
.event-card:hover {
    box-shadow:0 4px 10px rgba(0,0,0,.14);
}
.today { border:1.5px solid #000; }

.event-month {
    font-size:10px;
    font-weight:700;
    color:#666;
}
.event-day {
    font-size:20px;
    font-weight:700;
    line-height:1;
}
.event-category {
    font-size:12px;
    font-weight:700;
    margin-top:4px;
}
.event-time {
    font-size:10px;
    color:#555;
}
.program-badge {
    display:inline-block;
    margin-top:4px;
    padding:1px 6px;
    font-size:10px;
    background:#e3f2fd;
    color:#0d47a1;
    border-radius:10px;
}
.section-title {
    font-size:18px;
    font-weight:700;
    margin:18px 0 10px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# EVENT CARD
# ==================================================
def render_event_card(row):
    start = row["Start Date"]
    is_today = start.date() == date.today()

    month = start.strftime("%b").upper()
    day = start.strftime("%d")

    if str(row.get("All Day", "")).lower() == "true":
        time_html = "<div class='event-time'>All Day</div>"
    else:
        st_time = row.get("Start Time", "")
        en_time = row.get("End Time", "")
        time_html = f"<div class='event-time'>{st_time} – {en_time}</div>" if st_time or en_time else ""

    cls = "event-card today" if is_today else "event-card"

    st.markdown(f"""
    <div class="{cls}">
        <div class="event-month">{month}</div>
        <div class="event-day">{day}</div>
        {time_html}
        <div class="event-category">{row["Category"]}</div>
        <div class="program-badge">{row["Program"]}</div>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# ADMIN LOGIN
# ==================================================
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

# ==================================================
# ADMIN PANEL
# ==================================================
elif st.session_state.page == "admin":

    st.subheader("🛠 Admin Panel")

    raw_df = load_events()   # keep raw data for saving

    df = raw_df.copy()      # cleaned copy ONLY for display
    
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.dropna(subset=["Start Date", "End Date"])
    
    if not df.empty:
        df["Status"] = df.apply(event_status, axis=1)


    # ---- SUMMARY ----
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Events", len(df))
    c2.metric("Today", len(df[df["Start Date"].dt.date == date.today()]))
    c3.metric("Upcoming", len(df[df["Status"] == "Upcoming"]))

    # ---- ADD EVENT ----
    with st.expander("➕ Add Event", expanded=True):
        with st.form("add"):
            program = st.selectbox("Program", PROGRAMS)
            category = st.selectbox("Category", EVENT_CATEGORIES)
            title = st.text_input("Event Description")

            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start Date")
            end_date = c2.date_input("End Date", min_value=start_date)

            all_day = st.checkbox("All-day Event")

            if not all_day:
                t1, t2 = st.columns(2)
                start_time = t1.time_input("Start Time", time(10, 0))
                end_time = t2.time_input("End Time", time(17, 0))
            else:
                start_time = end_time = None

            add = st.form_submit_button("Add Event")

        if add and title.strip():
            new_row = {
                "EventID": next_event_id(df),
                "Program": program,
                "Category": category,
                "Title": title,
                "Start Date": start_date,
                "End Date": end_date,
                "Start Time": start_time.strftime("%I:%M %p") if start_time else "",
                "End Time": end_time.strftime("%I:%M %p") if end_time else "",
                "All Day": str(all_day)
            }
            raw_df = load_events()  # always append to RAW data

            raw_df = pd.concat(
                [raw_df, pd.DataFrame([new_row])],
                ignore_index=True
            )

save_events(raw_df)
st.success("Event added successfully")
st.rerun()


    # ---- MANAGE EVENTS ----
    st.divider()
    st.subheader("📋 Manage Events")

    if df.empty:
        st.info("No events available")
    else:
        for _, r in df.sort_values("Start Date").iterrows():
            with st.expander(f"{r['Program']} – {r['Title']}"):
                st.write(f"📅 {r['Start Date'].date()} → {r['End Date'].date()}")
                st.write("⏱️ All Day" if r["All Day"] == "True"
                         else f"⏱️ {r.get('Start Time','')} – {r.get('End Time','')}")

                c1, c2 = st.columns(2)
                if c1.button("✏️ Edit", key=f"edit_{r['EventID']}"):
                    st.session_state.edit_id = r["EventID"]
                    st.session_state.page = "edit"
                    st.rerun()
                if c2.button("❌ Delete", key=f"del_{r['EventID']}"):
                    df = df[df["EventID"] != r["EventID"]]
                    save_events(df)
                    st.rerun()

    if st.button("Logout"):
        st.session_state.page = "user"
        st.rerun()

# ==================================================
# EDIT EVENT
# ==================================================
elif st.session_state.page == "edit":

    df = load_events()
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")

    e = df[df["EventID"] == st.session_state.edit_id].iloc[0]

    st.subheader("✏️ Edit Event")

    with st.form("edit"):
        program = st.selectbox("Program", PROGRAMS, index=PROGRAMS.index(e["Program"]))
        category = st.selectbox("Category", EVENT_CATEGORIES, index=EVENT_CATEGORIES.index(e["Category"]))
        title = st.text_input("Title", value=e["Title"])

        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", value=e["Start Date"])
        end_date = c2.date_input("End Date", value=e["End Date"])

        all_day = st.checkbox("All-day Event", value=(e["All Day"] == "True"))

        if not all_day:
            t1, t2 = st.columns(2)
            start_time = t1.time_input("Start Time", time(10, 0))
            end_time = t2.time_input("End Time", time(17, 0))
        else:
            start_time = end_time = None

        update = st.form_submit_button("Update")

    if update:
        df.loc[df["EventID"] == e["EventID"]] = [
            e["EventID"], program, category, title,
            start_date, end_date,
            start_time.strftime("%I:%M %p") if start_time else "",
            end_time.strftime("%I:%M %p") if end_time else "",
            str(all_day)
        ]
        save_events(df)
        st.session_state.page = "admin"
        st.rerun()

# ==================================================
# USER LANDING PAGE
# ==================================================
else:

    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔐 Admin Login"):
            st.session_state.page = "admin_login"
            st.rerun()

    st.markdown("## 📅 Upcoming Events")

    program = st.selectbox("Filter by Program", ["All Programs"] + PROGRAMS)

    view = st.radio("View", ["Cards", "Weekly", "Monthly"], horizontal=True)

    df = load_events()

    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.dropna(subset=["Start Date", "End Date"])
    df["Status"] = df.apply(event_status, axis=1)
    df = df[df["Status"] != "Closed"]

    if program != "All Programs":
        df = df[df["Program"] == program]

    df = df.sort_values("Start Date")

    today_df = df[df["Start Date"].dt.date == date.today()]
    future_df = df[df["Start Date"].dt.date != date.today()]

    if not today_df.empty:
        st.markdown("<div class='section-title'>📌 Today</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (_, r) in enumerate(today_df.iterrows()):
            with cols[i % 3]:
                render_event_card(r)

    if view == "Cards":
        future_df["Month"] = future_df["Start Date"].dt.strftime("%B %Y")
        for m, grp in future_df.groupby("Month"):
            st.markdown(f"<div class='section-title'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(grp.iterrows()):
                with cols[i % 3]:
                    render_event_card(r)

    elif view == "Weekly":
        future_df["Week"] = future_df["Start Date"].dt.strftime("Week %U")
        for w, grp in future_df.groupby("Week"):
            st.markdown(f"<div class='section-title'>{w}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(grp.iterrows()):
                with cols[i % 3]:
                    render_event_card(r)

    elif view == "Monthly":
        future_df["Month"] = future_df["Start Date"].dt.strftime("%B %Y")
        for m, grp in future_df.groupby("Month"):
            st.markdown(f"<div class='section-title'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(grp.iterrows()):
                with cols[i % 3]:
                    render_event_card(r)
