# utils/analysis.py
from __future__ import annotations
import pandas as pd

def _explode_by_days(df: pd.DataFrame) -> pd.DataFrame:
    if "Days" not in df.columns:
        return df.copy()
    d = df.copy()
    d["Days"] = d["Days"].fillna("").astype(str)
    rows = []
    for _, r in d.iterrows():
        days = list(str(r["Days"]))
        if not days:
            rows.append(r)
            continue
        for dd in days:
            r2 = r.copy()
            r2["Day"] = dd
            rows.append(r2)
    return pd.DataFrame(rows)

def _parse_times(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["Start_dt"] = pd.to_datetime(d["Start Time"], errors="coerce")
    d["End_dt"]   = pd.to_datetime(d["End Time"], errors="coerce")
    d["duration_hours"] = (d["End_dt"] - d["Start_dt"]).dt.total_seconds() / 3600.0
    d["duration_hours"] = d["duration_hours"].clip(lower=0).fillna(0)
    return d

def detect_room_conflicts(course_df: pd.DataFrame) -> pd.DataFrame:
    if course_df is None or course_df.empty:
        return pd.DataFrame(columns=["Location","Day","CourseID_A","CourseID_B","Start_A","End_A","Start_B","End_B"])
    d = _explode_by_days(course_df)
    d = _parse_times(d)
    d = d[d["Location"].astype(str).str.strip() != ""].copy()
    d = d.dropna(subset=["Start_dt","End_dt"])
    if d.empty:
        return pd.DataFrame(columns=["Location","Day","CourseID_A","CourseID_B","Start_A","End_A","Start_B","End_B"])

    out_rows = []
    for (loc, day), g in d.groupby(["Location","Day"]):
        g = g.sort_values("Start_dt")
        arr = g[["CourseID","Start_dt","End_dt"]].values
        for i in range(len(arr)):
            A_id, A_s, A_e = arr[i]
            for j in range(i+1, len(arr)):
                B_id, B_s, B_e = arr[j]
                if B_s < A_e:
                    out_rows.append({
                        "Location": loc, "Day": day,
                        "CourseID_A": A_id, "CourseID_B": B_id,
                        "Start_A": A_s, "End_A": A_e,
                        "Start_B": B_s, "End_B": B_e,
                    })
                else:
                    break
    return pd.DataFrame(out_rows)

def detect_instructor_conflicts(course_df: pd.DataFrame) -> pd.DataFrame:
    if course_df is None or course_df.empty:
        return pd.DataFrame(columns=["Instructor","Day","CourseID_A","CourseID_B","Start_A","End_A","Start_B","End_B"])
    d = _explode_by_days(course_df)
    d = _parse_times(d)
    d = d[d["Instructor"].astype(str).str.strip() != ""].copy()
    d = d.dropna(subset=["Start_dt","End_dt"])
    if d.empty:
        return pd.DataFrame(columns=["Instructor","Day","CourseID_A","CourseID_B","Start_A","End_A","Start_B","End_B"])

    out_rows = []
    for (inst, day), g in d.groupby(["Instructor","Day"]):
        g = g.sort_values("Start_dt")
        arr = g[["CourseID","Start_dt","End_dt"]].values
        for i in range(len(arr)):
            A_id, A_s, A_e = arr[i]
            for j in range(i+1, len(arr)):
                B_id, B_s, B_e = arr[j]
                if B_s < A_e:
                    out_rows.append({
                        "Instructor": inst, "Day": day,
                        "CourseID_A": A_id, "CourseID_B": B_id,
                        "Start_A": A_s, "End_A": A_e,
                        "Start_B": B_s, "End_B": B_e,
                    })
                else:
                    break
    return pd.DataFrame(out_rows)

def _expand_for_utilization(df: pd.DataFrame) -> pd.DataFrame:
    d = _explode_by_days(df)
    d = _parse_times(d)
    d["hours"] = d["duration_hours"].fillna(0)
    return d

def calculate_room_utilization(course_df: pd.DataFrame, campus_rooms_df: pd.DataFrame, standard_hours_per_week: float = 40.0) -> pd.DataFrame:
    if campus_rooms_df is None or campus_rooms_df.empty:
        return pd.DataFrame(columns=["Location","Stations","Room Type","Room Size Category","scheduled_hours_per_week","utilization_pct"])
    if course_df is None or course_df.empty:
        base = campus_rooms_df.copy().rename(columns={"Room ID":"Location"})
        base["scheduled_hours_per_week"] = 0.0
        base["utilization_pct"] = 0.0
        return base[["Location","Stations","Room Type","Room Size Category","scheduled_hours_per_week","utilization_pct"]]

    exp = _expand_for_utilization(course_df)
    sched = exp.groupby("Location", as_index=False)["hours"].sum().rename(columns={"hours":"scheduled_hours_per_week"})
    base = campus_rooms_df[["Room ID","Stations","Room Type","Room Size Category"]].copy().rename(columns={"Room ID":"Location"})
    out = base.merge(sched, on="Location", how="left")
    out["scheduled_hours_per_week"] = out["scheduled_hours_per_week"].fillna(0.0)
    out["utilization_pct"] = (out["scheduled_hours_per_week"] / float(max(standard_hours_per_week, 0.001))) * 100.0
    return out

def summarize_utilization(util_df: pd.DataFrame) -> pd.DataFrame:
    if util_df is None or util_df.empty:
        return pd.DataFrame(columns=["Room Type","Room Size Category","Rooms","Avg Util %"])
    g = util_df.groupby(["Room Type","Room Size Category"], as_index=False).agg(
        Rooms=("Location","nunique"),
        Avg_Util=("utilization_pct","mean"),
    )
    g["Avg Util %"] = g["Avg_Util"].round(1)
    return g[["Room Type","Room Size Category","Rooms","Avg Util %"]]
