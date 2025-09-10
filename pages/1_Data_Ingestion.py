# pages/1_Data_Ingestion.py
import streamlit as st
from utils.file_handlers import load_excel, load_pdf_text, analyze_excel_structure

st.title("Step 1: Upload Source Files")

uploaded_files = st.file_uploader(
    "Upload Excel schedules & building lookup (and optional PDFs)",
    accept_multiple_files=True
)

if "RAW_FILES" not in st.session_state:
    st.session_state["RAW_FILES"] = {}

if uploaded_files:
    for f in uploaded_files:
        data = f.read()
        if f.type in ("application/pdf",) or f.name.lower().endswith(".pdf"):
            txt = load_pdf_text(data)
            st.session_state["RAW_FILES"][f.name] = {"type": "pdf", "text": txt}
            st.success(f"PDF loaded: {f.name}")
        else:
            try:
                sheets = load_excel(data, f.name)
                st.session_state["RAW_FILES"][f.name] = {"type": "excel", "sheets": sheets}
                st.success(f"Excel loaded: {f.name}")
                st.dataframe(analyze_excel_structure(sheets))
            except Exception as e:
                st.error(f"Failed to load {f.name}: {e}")

st.info("Go to **Step 2: Transformations** when done.")
