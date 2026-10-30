"""
Admin Panel for Akashvani v1.4
Password-protected admin interface with diagnostics and dashboard tabs
Access: https://akashvani.cxloop.co/🔐_Admin
"""

import streamlit as st
from datetime import datetime
import os
import sys

try:
    from st_keyup import st_keyup
except ImportError:
    st_keyup = None

PASSWORD_DEBOUNCE_MS = 500

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
    
    def password_entered(password):
        """Checks whether a password entered by the user is correct."""
        st.session_state["password_correct"] = (
            password == st.secrets.get("admin", {}).get("password", "admin123")
        )

    def render_password_input():
        password_input = st_keyup if st_keyup is not None else st.text_input
        password_options = {
            "type": "password",
            "key": "admin_password",
            "placeholder": "Enter password...",
        }
        if st_keyup is not None:
            password_options["debounce"] = PASSWORD_DEBOUNCE_MS
        return password_input("Enter Admin Password", **password_options)

    if not st.session_state.get("password_correct", False):
        st.markdown("### 🔐 Admin Access Required")
        password = render_password_input()
        if password:
            password_entered(password)
            if st.session_state["password_correct"]:
                return True
        #st.caption("⚠️ This area is restricted to administrators only")
        #st.info("💡 **Hint:** Check `.streamlit/secrets.toml` for the admin password")
        if "password_correct" in st.session_state:
            st.error("❌ Incorrect password. Access denied.")
        return False

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
tab_labels = [
    "📊 Analytics Dashboard",
    "📈 Charts",
    "🔍 System Diagnostics",
    "🧪 Test Suite",
]

tabs = st.tabs(tab_labels)
tab1, tab2, tab3, tab4 = tabs

# ===== TAB 1: DASHBOARD =====
with tab1:
    # Import and run dashboard module
    try:
        from pages.admin.dashboard import show_dashboard
        show_dashboard()
        
    except Exception as e:
        st.error(f"❌ Failed to load dashboard module: {e}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

# ===== TAB 2: CHARTS =====
with tab2:
    try:
        from pages.admin.charts import show_charts
        show_charts()

    except Exception as e:
        st.error(f"❌ Failed to load admin charts module: {e}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

# ===== TAB 3: DIAGNOSTICS =====
with tab3:
    try:
        from pages.admin.diagnostics import show_diagnostics
        show_diagnostics()
    except Exception as e:
        st.error(f"❌ Failed to load diagnostics module: {e}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

# ===== TAB 4: TEST SUITE =====
with tab4:
    try:
        from pages.admin.tests import show_tests
        show_tests()
    except Exception as e:
        st.error(f"❌ Failed to load test suite module: {e}")
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