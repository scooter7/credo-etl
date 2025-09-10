# utils/file_handlers.py
from __future__ import annotations
import io
from typing import Dict, List, Optional
import pandas as pd

# Try optional PDF backends lazily to avoid hard dependency
try:
    # Only bind a callable name; don't import module at top-level if unavailable
    from pdfminer.high_level import extract_text as _pdfminer_extract_text
    _HAS_PDFMINER = True
except Exception:
    _pdfminer_extract_text = None
    _HAS_PDFMINER = False

try:
    import PyPDF2 as _PyPDF2
    _HAS_PYPDF2 = True
except Exception:
    _PyPDF2 = None
    _HAS_PYPDF2 = False


# --------- Simple loaders ---------
def load_excel(file_bytes: bytes, filename: str) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    return {s: xls.parse(s, header=0) for s in xls.sheet_names}


def load_pdf_text(file_bytes: bytes) -> str:
    """
    Best-effort PDF text extraction.
    Prefers pdfminer.six if installed, falls back to PyPDF2, otherwise returns "".
    """
    if _HAS_PDFMINER and _pdfminer_extract_text is not None:
        with io.BytesIO(file_bytes) as fh:
            try:
                return _pdfminer_extract_text(fh) or ""
            except Exception:
                # fall through to next backend
                pass

    if _HAS_PYPDF2 and _PyPDF2 is not None:
        try:
            reader = _PyPDF2.PdfReader(io.BytesIO(file_bytes))
            chunks = []
            for page in reader.pages:
                try:
                    chunks.append(page.extract_text() or "")
                except Exception:
                    chunks.append("")
            return "\n".join(chunks).strip()
        except Exception:
            return ""

    # No PDF backend available; return empty so app continues
    return ""


# --------- Analyze sheets ---------
def analyze_excel_structure(sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in sheets.items():
        rows.append(
            {
                "sheet": name,
                "rows": len(df),
                "cols": len(df.columns),
                "columns_preview": [str(c) for c in df.columns[:10]],
            }
        )
    return pd.DataFrame(rows)


# --------- Detect lookup sheet ---------
def detect_bldg_lookup_sheet(sheets: Dict[str, pd.DataFrame]) -> Optional[str]:
    best = None
    best_score = -1
    for name, df in sheets.items():
        cols = {str(c).strip().lower() for c in df.columns}
        score = 0
        if {"building", "room #"} <= cols or {"bldg", "room"}.issubset(cols):
            score += 2
        if "asf" in cols or "sf" in cols:
            score += 1
        if "space use" in cols or "room type" in cols or "use" in cols:
            score += 1
        if score > best_score:
            best_score = score
            best = name
    return best if best_score >= 2 else None


def guess_bldg_column_map(df: pd.DataFrame) -> Dict[str, str]:
    cn = {str(c).strip().lower(): c for c in df.columns}

    def pick(*aliases):
        for a in aliases:
            if a in cn:
                return cn[a]
        return None

    return {
        "Building": pick("building", "bldg", "building code", "bldg code"),
        "Room": pick("room #", "room", "rm", "number"),
        "ASF": pick("asf", "sf", "area", "assignable square feet"),
        "Capacity": pick("capacity", "stations", "seats", "seat capacity", "max capacity"),
        "Room Type": pick("room type", "space use", "use", "type"),
        "Registrar": pick("registrar", "registrar scheduled", "scheduled by registrar"),
    }


def load_bldg_room_lookup(
    sheets: Dict[str, pd.DataFrame],
    sheet_name: Optional[str] = None,
    column_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    if sheet_name is None:
        sheet_name = detect_bldg_lookup_sheet(sheets)
        if sheet_name is None:
            raise ValueError("No building/room lookup sheet found.")
    df = sheets[sheet_name].copy()
    if column_map is None:
        column_map = guess_bldg_column_map(df)

    if not column_map.get("Building") or not column_map.get("Room"):
        raise ValueError(f"Missing required mapping for Building/Room. Columns: {list(df.columns)}")

    out = pd.DataFrame()
    out["Bldg"] = df[column_map["Building"]].astype(str).str.strip()
    out["Room"] = df[column_map["Room"]].astype(str).str.strip()

    out["ASF"] = (
        pd.to_numeric(df[column_map["ASF"]], errors="coerce").fillna(0)
        if column_map.get("ASF")
        else 0
    )

    out["Stations"] = (
        pd.to_numeric(df[column_map["Capacity"]], errors="coerce").fillna(0).astype(int)
        if column_map.get("Capacity")
        else 0
    )

    out["Room Type"] = (
        df[column_map["Room Type"]].astype(str).str.strip()
        if column_map.get("Room Type")
        else "Unknown"
    )

    out["RegistrarFlag"] = (
        df[column_map["Registrar"]].astype(str).str.strip()
        if column_map.get("Registrar")
        else ""
    )

    out["Room ID"] = (out["Bldg"].str.strip() + " " + out["Room"].str.strip()).str.strip()

    def size_cat(row):
        seats = row.get("Stations", 0)
        if seats > 0:
            if seats <= 15:
                return "A"
            if seats <= 25:
                return "B"
            if seats <= 35:
                return "C"
            if seats <= 49:
                return "D"
            if seats <= 75:
                return "E"
            return "F"
        asf = float(row.get("ASF", 0) or 0)
        if asf <= 300:
            return "A"
        if asf <= 500:
            return "B"
        if asf <= 700:
            return "C"
        if asf <= 900:
            return "D"
        if asf <= 1300:
            return "E"
        return "F"

    out["Room Size Category"] = out.apply(size_cat, axis=1)
    return out


def merge_class_schedule(schedules: List[pd.DataFrame]) -> pd.DataFrame:
    if not schedules:
        return pd.DataFrame()
    df = pd.concat(schedules, ignore_index=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df
