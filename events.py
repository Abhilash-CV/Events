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
        # Use the stored time format directly
        start_time = r["Start Time"] if pd.notna(r["Start Time"]) and r["Start Time"] != "" else "N/A"
        end_time = r["End Time"] if pd.notna(r["End Time"]) and r["End Time"] != "" else "N/A"
        time_html = f'{start_time} – {end_time}'

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
        # If already a string, return as is
        return t
    
    if isinstance(t, time):
        hour = t.hour
        minute = t.minute
        suffix = "AM" if hour < 12 else "PM"
        
        if hour == 0:
            hour = 12
        elif hour > 12:
            hour = hour - 12
        
        minute_str = f":{minute:02d}" if minute > 0 else ":00"
        return f"{hour}{minute_str} {suffix}"
    
    return str(t)

def parse_time_str(time_str):
    """Parse time string to datetime.time object"""
    if pd.isna(time_str) or time_str == "":
        return None
    
    try:
        # Handle 12-hour format
        time_str = str(time_str).strip().upper()
        if "AM" in time_str or "PM" in time_str:
            time_part = time_str.replace("AM", "").replace("PM", "").strip()
            if ":" in time_part:
                hour_str, minute_str = time_part.split(":")
                hour = int(hour_str)
                minute = int(minute_str) if minute_str else 0
            else:
                hour = int(time_part)
                minute = 0
            
            # Adjust for AM/PM
            if "PM" in time_str and hour < 12:
                hour += 12
            elif "AM" in time_str and hour == 12:
                hour = 0
            
            return time(hour, minute)
        # Handle 24-hour format
        elif ":" in time_str:
            hour_str, minute_str = time_str.split(":")
            hour = int(hour_str)
            minute = int(minute_str) if minute_str else 0
            return time(hour, minute)
    except:
        pass
    
    return None

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
            stime = etime = None

        add = st.form_submit_button("Add Event")

    if add:
        new = {
            "EventID": next_id(df),
            "Program": program,
            "Category": category,
            "Start Date": sd.strftime("%Y-%m-%d"),
            "End Date": ed.strftime("%Y-%m-%d"),
            "Start Time": format_12h(stime) if not allday and stime else "",
            "End Time": format_12h(etime) if not allday and etime else "",
            "All Day": str(allday)
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_events(df)
        st.success("Event added!")
        st.rerun()

    st.subheader("📋 Events")
    if df.empty:
        st.info("No events yet. Add your first event above.")
    else:
        for idx, r in df.iterrows():
            with st.expander(f'{r["Program"]} – {r["Category"]} (ID: {r["EventID"]})'):
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
                    st.success("Event deleted!")
                    st.rerun()

    st.divider()
    if st.button("⬅ Back to User View"):
        st.session_state.page = "user"
        st.rerun()

# ==================================================
# EDIT PAGE - FIXED TIME INPUTS
# ==================================================
elif st.session_state.page == "edit":

    df = load_events()
    if df.empty:
        st.error("No events to edit")
        st.session_state.page = "admin"
        st.rerun()
    
    r = df.iloc[st.session_state.edit_idx]

    st.header("✏️ Edit Event")

    # Parse existing times
    existing_allday = r["All Day"] == "True"
    
    # Parse existing time strings to time objects if they exist
    stime_existing = parse_time_str(r["Start Time"]) or time(10, 0)
    etime_existing = parse_time_str(r["End Time"]) or time(17, 0)

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
            start_idx = 0
            end_idx = 0
            if stime_existing:
                start_idx = min(range(len(time_options)), 
                              key=lambda i: abs(time_options[i].hour * 60 + time_options[i].minute - 
                                               (stime_existing.hour * 60 + stime_existing.minute)))
            if etime_existing:
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
            stime = etime = None

        update = st.form_submit_button("Update")
        cancel = st.form_submit_button("Cancel")

    if update:
        df.at[st.session_state.edit_idx, "Program"] = program
        df.at[st.session_state.edit_idx, "Category"] = category
        df.at[st.session_state.edit_idx, "Start Date"] = sd.strftime("%Y-%m-%d")
        df.at[st.session_state.edit_idx, "End Date"] = ed.strftime("%Y-%m-%d")
        df.at[st.session_state.edit_idx, "Start Time"] = (
            format_12h(stime) if not allday and stime else ""
        )
        df.at[st.session_state.edit_idx, "End Time"] = (
            format_12h(etime) if not allday and etime else ""
        )
        df.at[st.session_state.edit_idx, "All Day"] = str(allday)
    
        save_events(df)
        st.success("Event updated!")
        st.session_state.page = "admin"
        st.rerun()
    
    if cancel:
        st.session_state.page = "admin"
        st.rerun()

    if st.button("⬅ Back to Admin"):
        st.session_state.page = "admin"
        st.rerun()

# ==================================================
# USER PAGE - FIXED FILTERING
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
        st.info("No events available. Please add events in the Admin panel.")
        st.stop()

    # ---- Debug: Show raw data ----
    with st.expander("🔧 Debug: Show raw data"):
        st.write("Raw events data:")
        st.dataframe(df)
        st.write(f"Total events: {len(df)}")
        if not df.empty:
            st.write(f"Date range: {df['Start Date'].min()} to {df['End Date'].max()}")

    # ---- Clean and prepare data ----
    # Convert date columns
    try:
        df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce").dt.normalize()
        df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce").dt.normalize()
    except Exception as e:
        st.error(f"Error parsing dates: {e}")
        st.dataframe(df)
        st.stop()
    
    # Remove rows with invalid dates
    df = df[df["Start Date"].notna() & df["End Date"].notna()].copy()
    
    if df.empty:
        st.info("No valid events with proper dates.")
        st.stop()

    # Sort by Start Date
    df = df.sort_values("Start Date").reset_index(drop=True)

    # ---- Filters ----
    st.subheader("🔍 Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search = st.text_input("Search by name")
    with f2:
        program = st.selectbox("Program", ["All"] + PROGRAMS)
    with f3:
        category = st.selectbox("Category", ["All"] + CATEGORIES)
    with f4:
        dr = st.date_input("Date Range", [])

    # ---- Show all events toggle ----
    show_all = st.checkbox("Show all events (including past events)", value=True)

    # Apply date filtering if not showing all
    filtered_df = df.copy()
    
    if not show_all:
        today = pd.Timestamp.today().normalize()
        # Show events that end today or in the future
        filtered_df = filtered_df[filtered_df["End Date"] >= today].copy()
    
    # Apply other filters
    if search:
        filtered_df = filtered_df[
            filtered_df["Program"].str.contains(search, case=False) |
            filtered_df["Category"].str.contains(search, case=False)
        ]
    
    if program != "All":
        filtered_df = filtered_df[filtered_df["Program"] == program]
    
    if category != "All":
        filtered_df = filtered_df[filtered_df["Category"] == category]
    
    if len(dr) == 2:
        filtered_df = filtered_df[
            (filtered_df["Start Date"].dt.date >= dr[0]) &
            (filtered_df["End Date"].dt.date <= dr[1])
        ]

    # ---- View selection ----
    st.subheader("📊 View Options")
    view = st.radio("Select View", ["Cards", "Weekly", "Monthly", "Calendar", "Table"], 
                   horizontal=True, index=0)

    # ---- Debug: Show filtered data ----
    with st.expander("🔧 Debug: Show filtered data"):
        st.write(f"Filtered events: {len(filtered_df)}")
        st.dataframe(filtered_df)
        if not filtered_df.empty:
            st.write(f"Filtered date range: {filtered_df['Start Date'].min()} to {filtered_df['End Date'].max()}")

    # ---- Export ----
    if not filtered_df.empty:
        st.download_button(
            "📄 Download PDF", 
            export_pdf(filtered_df), 
            "events.pdf",
            help="Download all filtered events as PDF"
        )
    else:
        st.info("No events match your filters")

    # ---- Display events ----
    st.divider()
    
    if filtered_df.empty:
        st.warning("No events to display. Try adjusting your filters or check if events exist.")
        
        # Show what might be wrong
        if not show_all and not df.empty:
            today = pd.Timestamp.today().normalize()
            future_events = df[df["End Date"] >= today]
            st.write(f"You have {len(future_events)} future/ongoing events.")
            
            past_events = df[df["End Date"] < today]
            if len(past_events) > 0:
                st.write(f"You have {len(past_events)} past events. Check 'Show all events' to see them.")
    else:
        st.success(f"Showing {len(filtered_df)} event(s)")
        
        if view == "Table":
            # Simple table view for debugging
            display_df = filtered_df.copy()
            display_df["Start Date"] = display_df["Start Date"].dt.strftime("%Y-%m-%d")
            display_df["End Date"] = display_df["End Date"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df[["Program", "Category", "Start Date", "End Date", "Start Time", "End Time", "All Day"]])
        
        elif view == "Cards":
            # Group by month
            filtered_df["Month"] = filtered_df["Start Date"].dt.strftime("%B %Y")
            
            for month, month_group in filtered_df.groupby("Month", sort=False):
                st.markdown(f"<div class='section'>{month}</div>", unsafe_allow_html=True)
                
                # Create columns for cards
                cols = st.columns(6)
                for idx, (_, event) in enumerate(month_group.iterrows()):
                    with cols[idx % 6]:
                        card(event)
        
        elif view == "Weekly":
            # Group by week
            filtered_df["Week"] = filtered_df["Start Date"].dt.strftime("Week %U, %Y")
            
            for week, week_group in filtered_df.groupby("Week", sort=False):
                st.markdown(f"<div class='section'>{week}</div>", unsafe_allow_html=True)
                
                cols = st.columns(3)
                for idx, (_, event) in enumerate(week_group.iterrows()):
                    with cols[idx % 3]:
                        card(event)
        
        elif view == "Monthly":
            # Group by month-year
            filtered_df["MonthYear"] = filtered_df["Start Date"].dt.strftime("%B %Y")
            
            for month_year, month_group in filtered_df.groupby("MonthYear", sort=False):
                st.markdown(f"<div class='section'>{month_year}</div>", unsafe_allow_html=True)
                
                cols = st.columns(4)
                for idx, (_, event) in enumerate(month_group.iterrows()):
                    with cols[idx % 4]:
                        card(event)
        
        elif view == "Calendar":
            st.subheader("📆 Calendar View")
            
            # Select month
            selected_month = st.date_input("Select month to view", date.today())
            
            # Create calendar
            month_start = selected_month.replace(day=1)
            month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            
            # Get first day of calendar (Sunday of the week containing month_start)
            first_day = month_start - timedelta(days=month_start.weekday())
            
            # Create calendar grid
            st.markdown("### " + month_start.strftime("%B %Y"))
            
            # Day headers
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            cols = st.columns(7)
            for i, day_name in enumerate(day_names):
                cols[i].markdown(f"**{day_name}**")
            
            # Calendar days
            current_day = first_day
            for week in range(6):  # Max 6 weeks in calendar view
                cols = st.columns(7)
                for day_idx in range(7):
                    with cols[day_idx]:
                        # Check if day is in current month
                        is_current_month = month_start.month == current_day.month
                        day_style = ""
                        
                        if current_day.date() == date.today():
                            day_style = "border: 2px solid red; padding: 2px;"
                        
                        # Display day number
                        day_text = f"<div style='{day_style}'>{current_day.day}</div>"
                        
                        # Get events for this day
                        day_events = filtered_df[
                            (filtered_df["Start Date"].dt.date <= current_day.date()) &
                            (filtered_df["End Date"].dt.date >= current_day.date())
                        ]
                        
                        if not day_events.empty:
                            st.markdown(day_text, unsafe_allow_html=True)
                            for _, event in day_events.iterrows():
                                st.markdown(
                                    f"<div class='program' title='{event['Category']}'>{event['Program']}</div>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown(day_text, unsafe_allow_html=True)
                            if is_current_month:
                                st.write("")  # Empty space for alignment
                    
                    current_day += timedelta(days=1)
                
                # Stop if we've passed the month end
                if current_day.date() > month_end.date():
                    break

    # ---- Statistics ----
    st.divider()
    if not df.empty:
        st.subheader("📈 Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Events", len(df))
        with col2:
            ongoing = len(df[df["End Date"] >= pd.Timestamp.today().normalize()])
            st.metric("Upcoming/Ongoing", ongoing)
        with col3:
            st.metric("Programs", df["Program"].nunique())
