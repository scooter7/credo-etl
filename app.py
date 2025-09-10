import streamlit as st

# ------------------------------------------------------------
# STREAMLIT APP CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(
    page_title="Instructional Space Tool",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------------------
# APP HEADER
# ------------------------------------------------------------
st.title("📊 Instructional Space Tool")
st.markdown("""
Welcome to the Instructional Space Tool.  
Use the sidebar to navigate through the workflow:
- **Step 1:** Upload source files  
- **Step 2:** Transform and structure data  
- **Step 3:** Analyze conflicts and utilization  
- **Step 4:** Export final Excel deliverable
""")

st.sidebar.success("Select a step to begin →")
