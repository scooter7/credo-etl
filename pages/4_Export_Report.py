# pages/4_Export_Report.py
import streamlit as st
from utils.reporting import create_full_deliverable

st.title("Step 4: Export Final Deliverable")

course_schedule = st.session_state.get("COURSE_SCHEDULE")
campus_rooms    = st.session_state.get("CAMPUS_ROOMS")
buildings       = st.session_state.get("CAMPUS_BUILDINGS")
departments     = st.session_state.get("ACADEMIC_DEPARTMENTS")
utilization     = st.session_state.get("UTILIZATION")
room_conflicts  = st.session_state.get("ROOM_CONFLICTS")
instr_conflicts = st.session_state.get("INSTR_CONFLICTS")

missing = [n for n,v in [
    ("Course Schedule", course_schedule),
    ("Campus Rooms", campus_rooms),
    ("Campus Buildings", buildings),
    ("Academic Departments", departments),
    ("Utilization", utilization),
    ("Room Conflicts", room_conflicts),
    ("Instructor Conflicts", instr_conflicts),
] if v is None]

if missing:
    st.warning(f"⚠️ Missing from session: {', '.join(missing)}. Please complete Steps 2–3.")
else:
    data = create_full_deliverable(
        course_schedule, campus_rooms, buildings, departments,
        utilization, room_conflicts, instr_conflicts
    )
    st.download_button(
        "Download Deliverable (.xlsx)",
        data=data,
        file_name="Instruction_Analysis_Deliverable.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
