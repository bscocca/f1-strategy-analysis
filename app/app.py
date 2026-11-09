"""F1 Strategy Explorer: tyre degradation and undercut analysis, 2023-2026.

Run from the project root:
    streamlit run app/app.py
"""

import streamlit as st

st.set_page_config(page_title="F1 Strategy Explorer", layout="wide")

pages = [
    st.Page("views/home.py", title="Home", default=True),
]

st.navigation(pages).run()