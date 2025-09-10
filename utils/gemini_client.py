import os
import streamlit as st
import google.generativeai as genai

MODEL_NAME = "gemini-2.5-pro"

def _get_key():
    # Prefer Streamlit secrets; fall back to env var for local dev
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.getenv("GEMINI_API_KEY")

def init_gemini():
    key = _get_key()
    if not key:
        raise ValueError("Gemini API key not found. Set st.secrets['GEMINI_API_KEY'] or env GEMINI_API_KEY.")
    genai.configure(api_key=key)
    return genai

def summarize_conflicts_with_gemini(room_conflicts_df, instructor_conflicts_df, utilization_df, extra_notes=""):
    """
    Send a compact prompt with conflict/utilization tables (as CSV snippets).
    """
    init_gemini()
    model = genai.GenerativeModel(MODEL_NAME)

    # Keep prompt compact
    def head_csv(df, n=50):
        if df is None or df.empty:
            return "(none)"
        return df.head(n).to_csv(index=False)

    prompt = f"""
You are assisting with campus instructional space scheduling QA.

Room conflicts (top rows):
{head_csv(room_conflicts_df)}

Instructor conflicts (top rows):
{head_csv(instructor_conflicts_df)}

Room utilization (top rows):
{head_csv(utilization_df)}

Notes:
{extra_notes}

Tasks:
1) Summarize the most impactful issues (conflicts and under/over utilization).
2) Provide prioritized, actionable recommendations (room swaps, schedule tweaks).
3) Call out any data hygiene issues you infer (missing times, ambiguous days).
Make it concise and skimmable.
"""
    resp = model.generate_content(prompt)
    return resp.text or "(no response)"
