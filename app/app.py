"""F1 Strategy Explorer: tyre degradation and undercut analysis, 2023-2026.

Run from the project root:
    streamlit run app/app.py
"""

import streamlit as st

st.set_page_config(page_title="F1 Strategy Explorer", layout="wide")

pages = [
    st.Page("views/home.py", title="Home", default=True),
    st.Page("views/degradation.py", title="Tyre degradation"),
    st.Page("views/undercut.py", title="Undercut calculator"),
]

st.navigation(pages).run()