# utils/transformations.py
from __future__ import annotations
from typing import List, Optional
import pandas as pd
import numpy as np

# ------------------------------ Utilities ------------------------------

DAY_ALIASES = {
    "m": "M", "mon": "M", "monday": "M",
    "t": "T", "tue": "T", "tu": "T", "tuesday": "T",
    "w": "W", "wed": "W", "wednesday": "W",
    "r": "R", "thu": "R", "thur": "R", "th": "R", "thursday": "R",
    "f": "F", "fri": "F", "friday": "F",
    "s": "S", "sat": "S", "saturday": "S",
    "u": "U", "sun": "U", "sunday": "U",
}

COURSE_ID_CANDIDATES = [
    "CourseID", "Course Id", "Course", "Course Number", "Course number",
    "CRSID", "COURSE", "Course & Section", "Course/Section", "Course and Section"
]

SECTION_CANDIDATES = ["Section", "SEC", "Sections", "Section Number", "Sect"]
TITLE_CANDIDATES   = ["Course Title", "Course Name", "Title", "Name"]
DEPT_CANDIDATES    = ["Dept", "Department", "DEPT", "Department Code", "Dept Code"]
INSTR_CANDIDATES   = ["Instructor", "Instructor(s)", "Faculty", "Professor"]
START_TIME_CANDS   = ["Start Time", "Begin", "Start", "Time Start"]
END_TIME_CANDS     = ["End Time", "End", "Stop", "Time End"]
DAYS_CANDS         = ["Days", "Day", "Days of Week"]
BLDG_CANDS         = ["Bldg", "Building", "Bldg Code", "Building Code"]
ROOM_CANDS         = ["Room", "Room #", "Rm", "Room Number"]
CAP_CANDS          = ["Course Capacity", "Max Capacity", "Max Enroll", "Capacity", "Cap"]
ENRL_CANDS         = ["Actual Enrolled", "10D Enroll", "10th D Enroll", "EOT Enroll", "Enroll", "Enrollment"]
SEATS_OVERALL_CANDS= ["Seats in Overall Stn Utilization", "Seats Overall", "Seats in Overall"]
START_DATE_CANDS   = ["Start Date", "Start", "Begin Date"]
END_DATE_CANDS     = ["End Date", "End"]

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _find_col(df: pd.DataFrame, cands: List[str]) -> Optional[str]:
    cols_norm = {c.lower(): c for c in df.columns}
    for c in cands:
        c0 = c.lower()
        if c0 in cols_norm:
            return cols_norm[c0]
    for c in df.columns:
        cl = c.lower()
        for pat in cands:
            if pat.lower() in cl:
                return c
    return None

def _concat_course_id(df: pd.DataFrame) -> pd.Series:
    course_col = _find_col(df, ["Course Number", "Course", "COURSE", "Course number"])
    sect_col   = _find_col(df, SECTION_CANDIDATES)
    if course_col and sect_col:
        return (df[course_col].astype(str).str.strip() + df[sect_col].astype(str).str.strip()).str.replace(r"\s+", "", regex=True)
    cid_col = _find_col(df, COURSE_ID_CANDIDATES)
    if cid_col:
        return df[cid_col].astype(str).str.strip()
    raise KeyError("Missing a course identifier. Provide Course Number + Section or a combined CourseID column.")

def _normalize_days(val: str) -> str:
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    s = s.replace("-", "").replace(" ", "").replace("/", "")
    s = s.replace("thur", "r").replace("thu", "r").replace("th", "r")
    s = s.replace("tue", "t").replace("tu", "t")
    out = []
    for ch in s:
        out.append(DAY_ALIASES.get(ch, ch.upper()))
    return "".join(out)

def _time_like_to_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

# ------------------------------ Main builders ------------------------------

def build_course_schedule(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normalized Course Schedule with columns:
    ['CourseID','Special','Course Title','Dept','Instructor','Start Time','End Time',
     'Days','Location','Bldg','Room','Course Capacity','Actual Enrolled',
     'Seats in Overall Stn Utilization','Start Date','End Date']
    """
    if df_raw is None or df_raw.empty:
        raise ValueError("Empty schedule dataframe provided.")
    df = _norm_cols(df_raw)

    out = pd.DataFrame()
    out["CourseID"] = _concat_course_id(df)
    out["Special"] = ""

    title_col = _find_col(df, TITLE_CANDIDATES)
    dept_col  = _find_col(df, DEPT_CANDIDATES)
    instr_col = _find_col(df, INSTR_CANDIDATES)
    start_col = _find_col(df, START_TIME_CANDS)
    end_col   = _find_col(df, END_TIME_CANDS)
    days_col  = _find_col(df, DAYS_CANDS)
    bldg_col  = _find_col(df, BLDG_CANDS)
    room_col  = _find_col(df, ROOM_CANDS)
    cap_col   = _find_col(df, CAP_CANDS)
    enr_col   = _find_col(df, ENRL_CANDS)
    seats_overall_col = _find_col(df, SEATS_OVERALL_CANDS)
    sdate_col = _find_col(df, START_DATE_CANDS)
    edate_col = _find_col(df, END_DATE_CANDS)

    out["Course Title"] = df[title_col].astype(str).str.strip() if title_col else ""
    out["Dept"] = df[dept_col].astype(str).str.strip() if dept_col else ""
    out["Instructor"] = df[instr_col].astype(str).str.strip() if instr_col else ""

    out["Start Time"] = df[start_col].map(_time_like_to_str) if start_col else ""
    out["End Time"]   = df[end_col].map(_time_like_to_str) if end_col else ""

    if days_col:
        out["Days"] = df[days_col].map(_normalize_days).str.replace(" ", "", regex=False)
    else:
        # Build from separate day flags if present
        day_flag_cols = [c for c in df.columns if c.lower() in ("mon","m","tue","tu","t","wed","w","thu","th","r","fri","f","sat","s","sun","u")]
        if day_flag_cols:
            def mk_days(row):
                letters = []
                for c in day_flag_cols:
                    val = str(row.get(c, "")).strip().lower()
                    if val in ("1","true","yes","y","x","✓"):
                        letters.append(DAY_ALIASES.get(c.lower(), c[:1].upper()))
                return "".join(letters)
            out["Days"] = df.apply(mk_days, axis=1)
        else:
            out["Days"] = ""

    out["Bldg"] = df[bldg_col].astype(str).str.strip() if bldg_col else ""
    out["Room"] = df[room_col].astype(str).str.strip() if room_col else ""
    out["Location"] = (out["Bldg"].astype(str).str.strip() + " " + out["Room"].astype(str).str.strip()).str.strip()

    out["Course Capacity"] = pd.to_numeric(df[cap_col], errors="coerce").fillna(0).astype(int) if cap_col else 0
    out["Actual Enrolled"] = pd.to_numeric(df[enr_col], errors="coerce").fillna(0).astype(int) if enr_col else 0
    out["Seats in Overall Stn Utilization"] = (
        pd.to_numeric(df[seats_overall_col], errors="coerce").fillna(0).astype(int)
        if seats_overall_col
        else out["Actual Enrolled"]
    )

    out["Start Date"] = df[sdate_col] if sdate_col else ""
    out["End Date"]   = df[edate_col] if edate_col else ""

    # Make stringy where Streamlit/PyArrow gets picky
    for c in ["Course Title","Dept","Instructor","Days","Location","Bldg","Room","Special","Start Date","End Date"]:
        out[c] = out[c].astype(str)

    return out

def build_campus_rooms(lookup_df: pd.DataFrame) -> pd.DataFrame:
    if lookup_df is None or lookup_df.empty:
        raise ValueError("Empty building/room lookup dataframe provided.")
    df = lookup_df.copy()

    for col in ["Room ID","Bldg","Room","Stations","Room Type","ASF","Room Size Category"]:
        if col not in df.columns:
            if col in ("Stations","ASF"):
                df[col] = 0
            elif col == "Room Type":
                df[col] = "Unknown"
            elif col == "Room Size Category":
                df[col] = "A"
            elif col == "Room ID":
                df[col] = (df["Bldg"].astype(str).str.strip() + " " + df["Room"].astype(str).str.strip()).str.strip()
            else:
                df[col] = ""

    df["Room ID"] = df["Room ID"].astype(str).str.strip()
    df["Bldg"] = df["Bldg"].astype(str).str.strip()
    df["Room"] = df["Room"].astype(str).str.strip()
    df["Room Type"] = df["Room Type"].astype(str).str.strip()
    df["Room Size Category"] = df["Room Size Category"].astype(str).str.strip()
    df["Stations"] = pd.to_numeric(df["Stations"], errors="coerce").fillna(0).astype(int)
    df["ASF"] = pd.to_numeric(df["ASF"], errors="coerce").fillna(0)

    return df[["Room ID","Bldg","Room","Stations","Room Type","ASF","Room Size Category"]].copy()

def build_campus_buildings(rooms_df: pd.DataFrame) -> pd.DataFrame:
    if rooms_df is None or rooms_df.empty:
        return pd.DataFrame(columns=["Bldg","Rooms","Total Stations","Total ASF"])
    df = rooms_df.copy()
    grp = df.groupby("Bldg", as_index=False).agg(
        Rooms=("Room","nunique"),
        Total_Stations=("Stations","sum"),
        Total_ASF=("ASF","sum"),
    )
    grp.rename(columns={"Total_Stations":"Total Stations","Total_ASF":"Total ASF"}, inplace=True)
    return grp

def build_academic_departments(course_df: pd.DataFrame) -> pd.DataFrame:
    if course_df is None or course_df.empty:
        return pd.DataFrame(columns=["Dept","Sections","Total Enrolled"])
    df = course_df.copy()
    if "Dept" not in df.columns:
        df["Dept"] = ""
    if "Actual Enrolled" not in df.columns:
        df["Actual Enrolled"] = 0
    grp = df.groupby("Dept", as_index=False).agg(
        Sections=("CourseID","nunique"),
        Total_Enrolled=("Actual Enrolled","sum"),
    )
    grp.rename(columns={"Total_Enrolled":"Total Enrolled"}, inplace=True)
    return grp

def build_rooms_inventory(rooms_df: pd.DataFrame) -> pd.DataFrame:
    if rooms_df is None or rooms_df.empty:
        return pd.DataFrame(columns=["Room ID","Desks","Tables","Chairs","Computers","AV","Wall","Other"])
    out = rooms_df[["Room ID"]].copy()
    for c in ["Desks","Tables","Chairs","Computers","AV","Wall","Other"]:
        out[c] = ""
    return out

def build_course_instructors(course_df: pd.DataFrame) -> pd.DataFrame:
    if course_df is None or course_df.empty:
        return pd.DataFrame(columns=["Instructor","Dept","Daily Hours (M-F)"])
    df = course_df.copy()
    out = df.groupby(["Instructor","Dept"], as_index=False).agg(sections=("CourseID","nunique"))
    out["Daily Hours (M-F)"] = ""
    return out
