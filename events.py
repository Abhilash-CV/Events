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

def next_id(df):
    return 1 if df.empty else int(df["EventID"].max()) + 1

# ==================================================
# STYLES (desktop + mobile)
# ==================================================
st.markdown("""
<style>
.card {
  background: #95d1fc;
  border-radius: 6px;
  padding: 2px 3px;
  text-align: center;
  box-shadow: 0 0.5px 3px rgba(0,0,0,.08);
  margin-bottom: 10px;
  color: #0b3558;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,.18);
  transform: translateY(-2px);
  transition: all 0.2s ease-in-out;
}
.today {border:1.5px solid #000;}
.month {font-size:10px;font-weight:700;color:#666;}
.day {font-size:20px;font-weight:700;}
.cat {font-size:12px;font-weight:700;margin-top:4px;}
.time {font-size:10px;color:#555;}
.program {
  margin-top:4px;font-size:10px;background:#47b0fc;color:#0d47a1;
  border-radius:10px;padding:1px 6px;display:inline-block;
}
.section {font-size:18px;font-weight:700;margin:18px 0 10px;}

@media (max-width: 768px) {
  .stColumns { flex-direction: column !important; }
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# CARD - FIXED TIME FORMATTING
# ==================================================
def card(r):
    s = pd.to_datetime(r["Start Date"])
    is_today = s.date() == date.today()
    cls = "card today" if is_today else "card"
    
    # Handle time display properly
    if r["All Day"] == "True":
        time_html = "All Day"
    else:
        # Convert times to proper format
        try:
            if isinstance(r["Start Time"], str) and isinstance(r["End Time"], str):
                # Try to parse existing times
                if ":" in r["Start Time"]:
                    # Already in HH:MM format
                    start_time = r["Start Time"]
                    end_time = r["End Time"]
                    time_html = f'{start_time} – {end_time}'
                else:
                    # Try 12-hour format
                    time_html = f'{r["Start Time"]} – {r["End Time"]}'
            else:
                time_html = "Time not set"
        except:
            time_html = "Time not set"

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
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    styles = getSampleStyleSheet()
    content = [Paragraph("<b>Admission Events</b><br/><br/>", styles["Title"])]

    for _, r in df.iterrows():
        txt = f"""
        <b>{r['Program']}</b> – {r['Category']}<br/>
        {r['Start Date']} to {r['End Date']}<br/><br/>
        """
        content.append(Paragraph(txt, styles["Normal"]))

    doc.build(content)
    buf.seek(0)
    return buf

# ==================================================
# TIME FORMATTING FUNCTIONS
# ==================================================
def format_12h(t):
    """Convert datetime.time to 12-hour format"""
    if pd.isna(t) or t == "":
        return ""
    if isinstance(t, str):
        try:
            # Try to parse the string
            if "AM" in t.upper() or "PM" in t.upper():
                return t  # Already in 12-hour format
            elif ":" in t:
                # Parse HH:MM format
                parts = t.split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                t = time(h, m)
            else:
                return t
        except:
            return t
    
    if isinstance(t, time):
        hour = t.hour
        minute = t.minute
        suffix = "AM" if hour < 12 else "PM"
        
        if hour == 0:
            hour = 12
        elif hour > 12:
            hour = hour - 12
        
        minute_str = f":{minute:02d}" if minute > 0 else ""
        return f"{hour}{minute_str} {suffix}"
    
    return str(t)

def format_24h(t):
    """Convert datetime.time to 24-hour format"""
    if pd.isna(t) or t == "":
        return ""
    if isinstance(t, time):
        return f"{t.hour:02d}:{t.minute:02d}"
    return str(t)

# ==================================================
# ADMIN PAGE - FIXED TIME INPUTS
# ==================================================
if st.session_state.page == "admin":

    st.header("🛠 Admin Panel")
    df = load_events()

    with st.form("add_event"):
        program = st.selectbox("Program", PROGRAMS)
        category = st.selectbox("Category", CATEGORIES)
        c1, c2 = st.columns(2)
        sd = c1.date_input("Start Date")
        ed = c2.date_input("End Date", min_value=sd)

        allday = st.checkbox("All Day")
        if not allday:
            t1, t2 = st.columns(2)
            # Create proper time options (every 30 minutes)
            time_options = [time(h, m) for h in range(24) for m in (0, 30)]
            time_str_options = [format_12h(t) for t in time_options]
            
            # Default to 10:00 AM and 5:00 PM
            default_start_idx = time_options.index(time(10, 0))
            default_end_idx = time_options.index(time(17, 0))
            
            stime_str = t1.selectbox("Start Time", time_str_options, index=default_start_idx)
            etime_str = t2.selectbox("End Time", time_str_options, index=default_end_idx)
            
            # Convert back to time objects
            stime = time_options[time_str_options.index(stime_str)]
            etime = time_options[time_str_options.index(etime_str)]
        else:
            stime = etime = time(0, 0)  # Default for storage

        add = st.form_submit_button("Add Event")

    if add:
        new = {
            "EventID": next_id(df),
            "Program": program,
            "Category": category,
            "Start Date": sd,
            "End Date": ed,
            "Start Time": format_12h(stime) if not allday else "",
            "End Time": format_12h(etime) if not allday else "",
            "All Day": str(allday)
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_events(df)
        st.success("Event added")
        st.session_state.page = "user" 
        st.rerun()

    st.subheader("📋 Events")
    for idx, r in df.iterrows():
        with st.expander(f'{r["Program"]} – {r["Category"]}'):
            st.write(f"**Dates:** {r['Start Date']} to {r['End Date']}")
            if r["All Day"] == "True":
                st.write("**Time:** All Day")
            else:
                st.write(f"**Time:** {r['Start Time']} – {r['End Time']}")
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ Edit", key=f"edit_{idx}"):
                st.session_state.edit_idx = idx
                st.session_state.page = "edit"
                st.rerun()
            if c2.button("❌ Delete", key=f"del_{idx}"):
                df = df.drop(idx).reset_index(drop=True)
                save_events(df)
                st.rerun()

    if st.button("Logout"):
        st.session_state.page = "user"
        st.rerun()

# ==================================================
# EDIT PAGE - FIXED TIME INPUTS
# ==================================================
elif st.session_state.page == "edit":

    df = load_events()
    r = df.iloc[st.session_state.edit_idx]

    st.header("✏️ Edit Event")

    # Parse existing times
    existing_allday = r["All Day"] == "True"
    
    # Parse existing time strings to time objects if they exist
    stime_existing = time(10, 0)  # Default
    etime_existing = time(17, 0)  # Default
    
    if not existing_allday and r["Start Time"] and r["End Time"]:
        try:
            # Try to parse 12-hour format
            for time_str, default in [(r["Start Time"], time(10, 0)), (r["End Time"], time(17, 0))]:
                if isinstance(time_str, str):
                    time_str = time_str.strip().upper()
                    if "AM" in time_str or "PM" in time_str:
                        # 12-hour format
                        parts = time_str.replace("AM", "").replace("PM", "").strip().split(":")
                        hour = int(parts[0])
                        minute = int(parts[1]) if len(parts) > 1 else 0
                        
                        if "PM" in time_str and hour < 12:
                            hour += 12
                        elif "AM" in time_str and hour == 12:
                            hour = 0
                        
                        if time_str == r["Start Time"]:
                            stime_existing = time(hour, minute)
                        else:
                            etime_existing = time(hour, minute)
        except:
            pass

    with st.form("edit_form"):
        program = st.selectbox("Program", PROGRAMS, index=PROGRAMS.index(r["Program"]))
        category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(r["Category"]))
        c1, c2 = st.columns(2)
        sd = c1.date_input("Start Date", pd.to_datetime(r["Start Date"]).date())
        ed = c2.date_input("End Date", pd.to_datetime(r["End Date"]).date())
        allday = st.checkbox("All Day", value=existing_allday)

        if not allday:
            # Create proper time options
            time_options = [time(h, m) for h in range(24) for m in (0, 30)]
            time_str_options = [format_12h(t) for t in time_options]
            
            # Find closest existing times in options
            start_idx = min(range(len(time_options)), 
                          key=lambda i: abs(time_options[i].hour * 60 + time_options[i].minute - 
                                           (stime_existing.hour * 60 + stime_existing.minute)))
            end_idx = min(range(len(time_options)), 
                         key=lambda i: abs(time_options[i].hour * 60 + time_options[i].minute - 
                                          (etime_existing.hour * 60 + etime_existing.minute)))
            
            t1, t2 = st.columns(2)
            stime_str = t1.selectbox("Start Time", time_str_options, index=start_idx)
            etime_str = t2.selectbox("End Time", time_str_options, index=end_idx)
            
            # Convert back to time objects
            stime = time_options[time_str_options.index(stime_str)]
            etime = time_options[time_str_options.index(etime_str)]
        else:
            stime = etime = time(0, 0)

        update = st.form_submit_button("Update")

    if update:
        df.at[st.session_state.edit_idx, "Program"] = program
        df.at[st.session_state.edit_idx, "Category"] = category
        df.at[st.session_state.edit_idx, "Start Date"] = sd
        df.at[st.session_state.edit_idx, "End Date"] = ed
        df.at[st.session_state.edit_idx, "Start Time"] = (
            format_12h(stime) if not allday else ""
        )
        df.at[st.session_state.edit_idx, "End Time"] = (
            format_12h(etime) if not allday else ""
        )
        df.at[st.session_state.edit_idx, "All Day"] = str(allday)
    
        save_events(df)
        st.success("Event updated")
        st.session_state.page = "admin"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "admin"
        st.rerun()

# ==================================================
# USER PAGE
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
        st.stop()

    # ---- Clean ----
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce").dt.normalize()
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce").dt.normalize()
    
    # Keep only rows with valid dates
    df = df[
        (df["Start Date"].notna()) &
        (df["End Date"].notna())
    ]
    
    if df.empty:
        st.info("No valid events available")
        st.stop()
    
    # Get today's date for filtering
    today = pd.Timestamp.today().normalize()
    
    # Show events that:
    # 1. Start today or in the future, OR
    # 2. Are currently ongoing (started before today and end today or in the future)
    df["End Date"] = pd.to_datetime(df["End Date"])
    
    # Filter events that are either upcoming or currently ongoing
    df = df[
        (df["Start Date"] <= df["End Date"]) &  # Ensure valid date range
        (
            (df["Start Date"] >= today) |  # Future events
            (df["End Date"] >= today)      # Ongoing events (including multi-day)
        )
    ]
    
    df = df.sort_values("Start Date")

    # ---- Filters ----
    f1, f2, f3, f4 = st.columns(4)
    search = f1.text_input("🔍 Search")
    program = f2.selectbox("Program", ["All"] + PROGRAMS)
    category = f3.selectbox("Category", ["All"] + CATEGORIES)
    dr = f4.date_input("Date Range", [])

    view = st.radio("View", ["Cards", "Weekly", "Monthly", "Calendar"], horizontal=True)

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

    # ---- Show all events toggle ----
    show_all = st.checkbox("Show all events (including past events)", value=False)
    if show_all:
        # Reload all events without date filtering
        df = load_events()
        df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce").dt.normalize()
        df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce").dt.normalize()
        df = df[(df["Start Date"].notna()) & (df["End Date"].notna())]
        df = df.sort_values("Start Date")
        
        # Reapply other filters
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
    if not df.empty:
        st.download_button("📄 Download PDF", export_pdf(df), "events.pdf")
    else:
        st.info("No events match your filters")

    # ---- Views ----
    if df.empty:
        st.warning("No events to display")
    elif view == "Cards":
        df["Month"] = df["Start Date"].dt.strftime("%B %Y")
        for m, g in df.groupby("Month"):
            st.markdown(f"<div class='section'>{m}</div>", unsafe_allow_html=True)
            cols = st.columns(6)
            for i, (_, r) in enumerate(g.iterrows()):
                with cols[i % 6]:
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
                day_class = "today" if d.date() == date.today() else ""
                st.markdown(f'<div class="{day_class}">{d.strftime("%d %b")}</div>', 
                          unsafe_allow_html=True)
                day_events = df[
                    (df["Start Date"].dt.date <= d.date()) & 
                    (df["End Date"].dt.date >= d.date())
                ]
                for _, r in day_events.iterrows():
                    st.markdown(
                        f"<div class='program'>{r['Program']}</div>",
                        unsafe_allow_html=True
                    )
