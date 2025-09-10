# pages/2_Transformations.py
import streamlit as st
import pandas as pd

from utils.file_handlers import (
    analyze_excel_structure,
    detect_bldg_lookup_sheet,
    load_bldg_room_lookup,
    merge_class_schedule,
)

from utils.transformations import (
    build_course_schedule,
    build_campus_rooms,
    build_campus_buildings,
    build_academic_departments,   # <-- exact name
    build_rooms_inventory,
    build_course_instructors,
)

st.title("Step 2: Transformations")

raw_files = st.session_state.get("RAW_FILES", {})
if not raw_files:
    st.warning("⚠️ Please upload files in Step 1 first.")
    st.stop()

# Collect candidate schedule sheets (very loose heuristic)
excel_schedules = []
for _, info in raw_files.items():
    if info["type"] != "excel":
        continue
    for sname, df in info["sheets"].items():
        cols = {str(c).strip().lower() for c in df.columns}
        if any(k in cols for k in ("times","days","rooms")) or any(k in cols for k in ("start time","end time")):
            excel_schedules.append(df)

st.subheader("1) Build Course Schedule")
try:
    merged = merge_class_schedule(excel_schedules)
    course_schedule = build_course_schedule(merged)
    st.session_state["COURSE_SCHEDULE"] = course_schedule
    st.success("✅ Course Schedule built.")
    st.dataframe(course_schedule.astype({c:"string" for c in course_schedule.columns if course_schedule[c].dtype=='object'}))
except Exception as e:
    st.error(f"❌ Error building Course Schedule: {e}")
    st.stop()

st.subheader("2) Build Campus Rooms (from Building Lookup)")
lookup_df = None
# Try auto-detect once
for fname, info in raw_files.items():
    if info["type"] != "excel":
        continue
    cand = detect_bldg_lookup_sheet(info["sheets"])
    if cand:
        try:
            lookup_df = load_bldg_room_lookup(info["sheets"], cand)
            st.caption(f"Auto-detected: {fname} :: {cand}")
            break
        except Exception as e:
            st.warning(f"Auto-detect failed on {fname}/{cand}: {e}")

if lookup_df is None:
    st.warning("Could not auto-detect a building lookup. Choose file/sheet manually.")
    excel_file_names = [k for k,v in raw_files.items() if v["type"]=="excel"]
    selected_file = st.selectbox("Select Excel file", options=excel_file_names)
    if selected_file:
        sheet_name = st.selectbox("Select sheet", options=list(raw_files[selected_file]["sheets"].keys()))
        if sheet_name:
            try:
                lookup_df = load_bldg_room_lookup(raw_files[selected_file]["sheets"], sheet_name)
            except Exception as e:
                st.error(f"❌ Error loading building lookup: {e}")
                st.stop()

try:
    campus_rooms = build_campus_rooms(lookup_df)
    st.session_state["CAMPUS_ROOMS"] = campus_rooms
    st.success("✅ Campus Rooms built.")
    st.dataframe(campus_rooms.astype({c:"string" for c in campus_rooms.columns if campus_rooms[c].dtype=='object'}))
except Exception as e:
    st.error(f"❌ Error building Campus Rooms: {e}")
    st.stop()

st.subheader("3) Buildings, Departments, Inventory, Instructors")
buildings = build_campus_buildings(campus_rooms)
st.session_state["CAMPUS_BUILDINGS"] = buildings
st.dataframe(buildings)

departments = build_academic_departments(course_schedule)
st.session_state["ACADEMIC_DEPARTMENTS"] = departments
st.dataframe(departments)

inventory = build_rooms_inventory(campus_rooms)
st.session_state["ROOMS_INVENTORY"] = inventory

instructors = build_course_instructors(course_schedule)
st.session_state["COURSE_INSTRUCTORS"] = instructors

st.info("Proceed to **Step 3: Analysis**.")
