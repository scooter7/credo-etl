# utils/reporting.py
from __future__ import annotations
import io
import pandas as pd

def create_full_deliverable(
    course_schedule: pd.DataFrame,
    campus_rooms: pd.DataFrame,
    buildings: pd.DataFrame,
    departments: pd.DataFrame,
    utilization: pd.DataFrame,
    room_conflicts: pd.DataFrame,
    instructor_conflicts: pd.DataFrame,
) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        course_schedule.to_excel(xw, sheet_name="Course Schedule", index=False)
        campus_rooms.to_excel(xw, sheet_name="Campus Rooms", index=False)
        buildings.to_excel(xw, sheet_name="Campus Buildings", index=False)
        departments.to_excel(xw, sheet_name="Academic Depts", index=False)
        utilization.to_excel(xw, sheet_name="Utilization", index=False)
        room_conflicts.to_excel(xw, sheet_name="Room Conflicts", index=False)
        instructor_conflicts.to_excel(xw, sheet_name="Instructor Conflicts", index=False)
    buf.seek(0)
    return buf.getvalue()
