"""
Admin Panel for Akashvani v1.4
Password-protected admin interface with diagnostics and dashboard tabs
Access: https://akashvani.cxloop.co/🔐_Admin
"""

import streamlit as st
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="🔐 Admin Panel - Akashvani",
    page_icon="https://akashvani.cxloop.co/favicon.ico",
    layout="wide",
)

# ===== PASSWORD PROTECTION =====
def check_password():
    """Returns True if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["admin_password"] == st.secrets.get("admin", {}).get("password", "admin123"):
            st.session_state["password_correct"] = True
            del st.session_state["admin_password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown("### 🔐 Admin Access Required")
        st.text_input(
            "Enter Admin Password", 
            type="password", 
            on_change=password_entered, 
            key="admin_password",
            placeholder="Enter password..."
        )
        #st.caption("⚠️ This area is restricted to administrators only")
        #st.info("💡 **Hint:** Check `.streamlit/secrets.toml` for the admin password")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.markdown("### 🔐 Admin Access Required")
        st.text_input(
            "Enter Admin Password", 
            type="password", 
            on_change=password_entered, 
            key="admin_password",
            placeholder="Enter password..."
        )
        st.error("❌ Incorrect password. Access denied.")
        return False
    else:
        # Password correct
        return True

if not check_password():
    st.stop()

# ===== LOGGED IN - SHOW ADMIN PANEL =====

# Header with logout button
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("🔐 Akashvani Admin Panel")
    st.markdown("**System Diagnostics & Analytics Dashboard**")
with header_col2:
    st.markdown("")
    st.markdown("")
    if st.button("🔓 Logout", type="primary", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# ===== TABS =====
tab1, tab2 = st.tabs(["🔍 System Diagnostics", "📊 Analytics Dashboard"])

# ===== TAB 1: DIAGNOSTICS =====
with tab1:
    # Import and run diagnostics module
    try:
        # Add admin subdirectory to path
        admin_path = os.path.join(os.path.dirname(__file__), 'admin')
        sys.path.insert(0, admin_path)
        
        from diagnostics import show_diagnostics
        show_diagnostics()
        
    except Exception as e:
        st.error(f"❌ Failed to load diagnostics module: {e}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

# ===== TAB 2: DASHBOARD =====
with tab2:
    # Import and run dashboard module
    try:
        # Add admin subdirectory to path
        admin_path = os.path.join(os.path.dirname(__file__), 'admin')
        sys.path.insert(0, admin_path)
        
        from dashboard import show_dashboard
        show_dashboard()
        
    except Exception as e:
        st.error(f"❌ Failed to load dashboard module: {e}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

# ===== FOOTER =====
st.markdown("---")
footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    st.caption("🔒 Admin Panel | Akashvani v1.4")
    st.caption("© 2026 CX Data & Analytics LLC")
    st.caption("📧 Support: support@cxloop.co")

with footer_col2:
    st.caption(f"👤 Logged in as: Admin")
    st.caption(f"🕐 Session: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
