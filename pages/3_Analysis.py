# pages/3_Analysis.py
import streamlit as st
from utils.analysis import (
    calculate_room_utilization,
    summarize_utilization,
    detect_room_conflicts,
    detect_instructor_conflicts,
)

st.title("Step 3: Analysis")

course_schedule = st.session_state.get("COURSE_SCHEDULE")
campus_rooms    = st.session_state.get("CAMPUS_ROOMS")

if course_schedule is None or campus_rooms is None:
    st.warning("⚠️ Please complete Step 2 first.")
    st.stop()

st.header("Room Utilization (Baseline)")
std_hours = st.number_input("Standard scheduled hours/week (per room)", min_value=1.0, max_value=80.0, value=40.0, step=1.0)
utilization = calculate_room_utilization(course_schedule, campus_rooms, std_hours)
st.session_state["UTILIZATION"] = utilization
st.dataframe(utilization)

st.header("Utilization Summary")
summary = summarize_utilization(utilization)
st.session_state["UTIL_SUMMARY"] = summary
st.dataframe(summary)

st.header("Conflicts")
with st.spinner("Detecting room conflicts..."):
    r_conf = detect_room_conflicts(course_schedule)
    st.session_state["ROOM_CONFLICTS"] = r_conf
st.dataframe(r_conf)

with st.spinner("Detecting instructor conflicts..."):
    i_conf = detect_instructor_conflicts(course_schedule)
    st.session_state["INSTR_CONFLICTS"] = i_conf
st.dataframe(i_conf)

st.info("Proceed to **Step 4: Export**.")
