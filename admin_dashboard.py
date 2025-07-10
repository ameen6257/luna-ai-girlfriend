Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import streamlit as st
import os
import json
import datetime
from secure_storage import load_access_codes, save_access_codes

st.set_page_config(page_title="Luna Admin Dashboard", layout="centered")
st.title("🔐 Luna Admin: Access Code Manager")

... ADMIN_EMAIL = "your_email@gmail.com"  # Change to your real Google email
... 
... email = st.text_input("Enter admin email to proceed")
... if email != ADMIN_EMAIL:
...     st.error("Access denied. This page is for admin only.")
...     st.stop()
... 
... codes = load_access_codes()
... 
... st.subheader("📜 Existing Access Codes")
... for code, info in codes.items():
...     col1, col2, col3 = st.columns([2, 2, 1])
...     col1.markdown(f"**🔑 {code}**")
...     col2.markdown(f"**{info['uses_left']} left** — Expires `{info['expires']}`")
...     if col3.button("🗑️ Delete", key=f"del_{code}"):
...         del codes[code]
...         save_access_codes(codes)
...         st.experimental_rerun()
... 
... st.subheader("➕ Add New Access Code")
... with st.form("add_code"):
...     new_code = st.text_input("Code (e.g. LUNA2026)")
...     uses = st.number_input("Uses Left", min_value=1, value=1)
...     expires = st.date_input("Expires On", min_value=datetime.date.today())
...     submit = st.form_submit_button("Add Code")
... 
...     if submit and new_code:
...         codes[new_code] = {
...             "uses_left": uses,
...             "expires": str(expires),
...             "used_by": []
...         }
...         save_access_codes(codes)
...         st.success(f"✅ Code {new_code} added.")
...         st.experimental_rerun()
... 
... st.download_button("📥 Download access_codes.json", data=json.dumps(codes, indent=2),
...                    file_name="access_codes_backup.json")
