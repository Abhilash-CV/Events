import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

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
st.session_state.setdefault("edit_idx", None)

# ==================================================
# DATA
# ==================================================
def load_events():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=COLUMNS)

def save_events(df):
    df.to_csv(DATA_FILE, index=False)

# ==================================================
# STYLES (Mobile friendly)
# ==================================================
st.markdown("""
<style>
.card {
  background:#fff; border-radius:8px; padding:8px; text-align:center;
  box-shadow:0 1px 6px rgba(0,0,0,.08); margin-bottom:10px;
}
.today { border:1.5px solid #000; }
.month { font-size:10px; font-weight:700; color:#666; }
.day { font-size:20px; font-weight:700; }
.cat { font-size:12px; font-weight:700; margin-top:4px; }
.time { font-size:10px; color:#555; }
.program {
  margin-top:4px; font-size:10px; background:#e3f2fd;
  color:#0d47a1; border-radius:10px; padding:1px 6px;
  display:inline-block;
}
.section { font-size:18px; font-weight:700; margin:18px 0 10px; }

/* Mobile */
@media (max-width: 768px) {
  .stColumns { flex-direction: column !important; }
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# CARD
# ==================================================
def card(r):
    s = pd.to_datetime(r["Start Date"])
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
# PDF EXPORT
# ==================================================
def export_pdf(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [Paragraph("<b>Admission Events</b><br/><br/>", styles["Title"])]

    for _, r in df.iterrows():
        txt = f"""
        <b>{r['Program']}</b> – {r['Category']}<br/>
        {r['Start Date']} to {r['End Date']}<br/><br/>
        """
        elements.append(Paragraph(txt, styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================================================
# USER PAGE
# ==================================================
if st.session_state.page == "user":

    st.header("📅 Upcoming Events")

    df = load_events()
    if df.empty:
        st.info("No events available")
        st.stop()

    # ---- Clean ----
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.dropna(subset=["Start Date", "End Date"])
    df = df[df["End Date"].dt.date >= date.today()]
    df = df.sort_values("Start Date")

    # ---- Filters ----
    col1, col2, col3, col4 = st.columns(4)

    search = col1.text_input("🔍 Search")
    program = col2.selectbox("Program", ["All"] + PROGRAMS)
    category = col3.selectbox("Category", ["All"] + CATEGORIES)
    dr = col4.date_input("Date Range", [])

    view = st.radio(
        "View",
        ["Cards", "Weekly", "Monthly", "Calendar"],
        horizontal=True
    )

    if search:
        df = df[df["Program"].str.contains(search, case=False) |
                df["Category"].str.contains(search, case=False)]

    if program != "All":
        df = df[df["Program"] == program]

    if category != "All":
        df = df[df["Category"] == category]

    if len(dr) == 2:
        df = df[(df["Start Date"].dt.date >= dr[0]) &
                (df["End Date"].dt.date <= dr[1])]

    # ---- Export ----
    pdf = export_pdf(df)
    st.download_button("📄 Download PDF", pdf, "events.pdf")

    # ---- Views ----
    if view == "Cards":
        df["Month"] = df["Start Date"].dt.strftime("%B %Y")
        for m, g in df.groupby("Month"):
            st.markdown(f"<div class='section'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(g.iterrows()):
                with cols[i % 3]:
                    card(r)

    elif view == "Weekly":
        df["Week"] = df["Start Date"].dt.strftime("Week %U")
        for w, g in df.groupby("Week"):
            st.markdown(f"<div class='section'>{w}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(g.iterrows()):
                with cols[i % 3]:
                    card(r)

    elif view == "Monthly":
        df["Month"] = df["Start Date"].dt.strftime("%B %Y")
        for m, g in df.groupby("Month"):
            st.markdown(f"<div class='section'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, (_, r) in enumerate(g.iterrows()):
                with cols[i % 3]:
                    card(r)

    elif view == "Calendar":
        st.subheader("📆 Calendar View")
        month = st.date_input("Select month", date.today()).replace(day=1)
        start = month - timedelta(days=month.weekday())
        days = [start + timedelta(days=i) for i in range(42)]

        cols = st.columns(7)
        for i, d in enumerate(days):
            with cols[i % 7]:
                st.caption(d.strftime("%d %b"))
                for _, r in df[df["Start Date"].dt.date == d.date()].iterrows():
                    st.markdown(
                        f"<div class='program'>{r['Program']}</div>",
                        unsafe_allow_html=True
                    )
