import streamlit as st
import pandas as pd
from datetime import date, time

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Admission Events", layout="wide")

DATA_FILE = "events.csv"

PROGRAMS = [
    "KEAM", "LLB 3 Year", "LLB 5 Year", "LLM",
    "PG Ayurveda", "PG Homoeo", "PG Nursing"
]

CATEGORIES = [
    "Online Application",
    "Memo Clearance",
    "Option Registration",
    "Provisional Category List",
    "Provisional Rank List",
    "Provisional Allotment",
    "Final Allotment"
]

COLUMNS = [
    "EventID", "Program", "Category",
    "Start Date", "End Date",
    "Start Time", "End Time", "All Day"
]

# ==================================================
# SESSION
# ==================================================
st.session_state.setdefault("page", "user")
st.session_state.setdefault("edit_id", None)

# ==================================================
# DATA LAYER (NO CLEANING HERE)
# ==================================================
def load_events():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)


def save_events(df):
    df.to_csv(DATA_FILE, index=False)


def next_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1


# ==================================================
# STATUS (DISPLAY ONLY)
# ==================================================
def status(start, end):
    today = date.today()
    if end < today:
        return "Closed"
    elif start > today:
        return "Upcoming"
    return "Active"


# ==================================================
# STYLES (COMPACT)
# ==================================================
st.markdown("""
<style>
.card {
    background:white;
    border-radius:8px;
    padding:8px;
    text-align:center;
    box-shadow:0 1px 6px rgba(0,0,0,.08);
    margin-bottom:10px;
}
.today { border:1.5px solid black; }
.month { font-size:10px; font-weight:700; color:#666; }
.day { font-size:20px; font-weight:700; }
.cat { font-size:12px; font-weight:700; margin-top:4px; }
.time { font-size:10px; color:#555; }
.program {
    margin-top:4px;
    font-size:10px;
    background:#e3f2fd;
    color:#0d47a1;
    border-radius:10px;
    padding:1px 6px;
    display:inline-block;
}
.section {
    font-size:18px;
    font-weight:700;
    margin:18px 0 10px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# CARD
# ==================================================
def card(r):
    s = pd.to_datetime(r["Start Date"])
    e = pd.to_datetime(r["End Date"])
    is_today = s.date() == date.today()

    cls = "card today" if is_today else "card"

    time_html = "All Day" if r["All Day"] == "True" else f'{r["Start Time"]} – {r["End Time"]}'

    st.markdown(f"""
    <div class="{cls}">
        <div class="month">{s.strftime('%b').upper()}</div>
        <div class="day">{s.strftime('%d')}</div>
        <div class="time">{time_html}</div>
        <div class="cat">{r["Category"]}</div>
        <div class="program">{r["Program"]}</div>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# ADMIN
# ==================================================
if st.session_state.page == "admin":

    st.header("🛠 Admin Panel")

    df = load_events()

    # ---------- SUMMARY ----------
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Today", len(df[pd.to_datetime(df["Start Date"], errors="coerce").dt.date == date.today()]))
    c3.metric("Upcoming", len(df[pd.to_datetime(df["Start Date"], errors="coerce").dt.date > date.today()]))

    # ---------- ADD ----------
    with st.form("add"):
        program = st.selectbox("Program", PROGRAMS)
        category = st.selectbox("Category", CATEGORIES)

        c1, c2 = st.columns(2)
        sd = c1.date_input("Start Date")
        ed = c2.date_input("End Date", min_value=sd)

        allday = st.checkbox("All Day")
        if not allday:
            t1, t2 = st.columns(2)
            stime = t1.time_input("Start Time", time(10, 0))
            etime = t2.time_input("End Time", time(17, 0))
        else:
            stime = etime = ""

        add = st.form_submit_button("Add Event")

    if add:
        new = {
            "EventID": next_id(df),
            "Program": program,
            "Category": category,
            "Start Date": sd,
            "End Date": ed,
            "Start Time": stime.strftime("%I:%M %p") if stime else "",
            "End Time": etime.strftime("%I:%M %p") if etime else "",
            "All Day": str(allday)
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_events(df)
        st.success("Event added")
        st.rerun()

    # ---------- LIST ----------
    st.subheader("📋 Events")
    for _, r in df.iterrows():
        with st.expander(f'{r["Program"]} – {r["Category"]}'):
            st.write(f'{r["Start Date"]} → {r["End Date"]}')
            if st.button("❌ Delete", key=f'del{r["EventID"]}'):
                df = df[df["EventID"] != r["EventID"]]
                save_events(df)
                st.rerun()

    if st.button("Logout"):
        st.session_state.page = "user"
        st.rerun()

# ==================================================
# USER
# ==================================================
else:

    col1, col2 = st.columns([8,2])
    with col2:
        if st.button("🔐 Admin"):
            st.session_state.page = "admin"
            st.rerun()

    st.header("📅 Upcoming Events")

    df = load_events()
    if df.empty:
        st.info("No events available")
    else:
        df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
        df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
        df = df.dropna(subset=["Start Date", "End Date"])
        df = df[df["End Date"].dt.date >= date.today()]
        df = df.sort_values("Start Date")

        today = df[df["Start Date"].dt.date == date.today()]
        future = df[df["Start Date"].dt.date != date.today()]

        if not today.empty:
            st.markdown("<div class='section'>📌 Today</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(today.iterrows()):
                with cols[i % 3]:
                    card(r)

        future["Month"] = future["Start Date"].dt.strftime("%B %Y")
        for m, g in future.groupby("Month"):
            st.markdown(f"<div class='section'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(g.iterrows()):
                with cols[i % 3]:
                    card(r)
