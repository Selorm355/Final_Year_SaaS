import streamlit as st

def inject_global_theme():
    """Injects the Orbit CRM light theme, removes top header line, and styles circular controls."""
    dark = st.session_state.get("dark_mode", False)
    
    bg_canvas = "#0F172A" if dark else "#F1F5F9"
    bg_surface = "#1E293B" if dark else "#FFFFFF"
    text_primary = "#F8FAFC" if dark else "#0F172A"
    text_secondary = "#94A3B8" if dark else "#64748B"
    input_bg = "#1E293B" if dark else "#FFFFFF"
    input_border = "#334155" if dark else "#CBD5E1"
    sidebar_bg = "#1E293B" if dark else "#FFFFFF"
    card_border = "rgba(255,255,255,0.08)" if dark else "#E2E8F0"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        /* Hide Streamlit default header, deploy button, running stop bar */
        header[data-testid="stHeader"], 
        [data-testid="stToolbar"], 
        [data-testid="stDecoration"], 
        [data-testid="stStatusWidget"],
        #MainMenu, 
        footer {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }}

        /* Canvas */
        .stApp {{
            background-color: {bg_canvas} !important;
            color: {text_primary} !important;
        }}

        .block-container {{
            padding-top: 1.8rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2.5rem !important;
            max-width: 1400px !important;
        }}

        /* Floating Sidebar Rail */
        [data-testid="stSidebar"] {{
            background-color: transparent !important;
            border: none !important;
            width: 78px !important;
            min-width: 78px !important;
            max-width: 78px !important;
            margin: 14px 0 14px 14px !important;
            height: calc(100vh - 28px) !important;
            box-shadow: none !important;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background-color: {sidebar_bg} !important;
            border-radius: 24px !important;
            border: 1px solid {card_border} !important;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05) !important;
            padding: 16px 8px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            height: calc(100vh - 28px) !important;
            box-sizing: border-box !important;
        }}

        /* Sidebar Buttons */
        [data-testid="stSidebar"] .stButton button {{
            width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            border-radius: 16px !important;
            padding: 0 !important;
            margin: 0 auto 8px auto !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1.35rem !important;
            background: transparent !important;
            border: 1px solid transparent !important;
            color: {text_secondary} !important;
            transition: all 0.2s ease !important;
        }}

        [data-testid="stSidebar"] .stButton button:hover {{
            background-color: #F1F5F9 !important;
            color: #4F46E5 !important;
        }}

        [data-testid="stSidebar"] .stButton button[kind="primary"] {{
            background-color: #4F46E5 !important;
            color: #FFFFFF !important;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.35) !important;
            border: none !important;
        }}

        /* Circular Action Buttons for Header */
        .circle-btn button {{
            width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background-color: {bg_surface} !important;
            border: 1.5px solid {card_border} !important;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05) !important;
            font-size: 1.15rem !important;
            color: {text_primary} !important;
            transition: all 0.2s ease !important;
        }}
        .circle-btn button:hover {{
            border-color: #4F46E5 !important;
            transform: scale(1.05);
        }}

        /* High Visibility Inputs & Dropdown */
        .stTextInput input, 
        .stSelectbox div[data-baseweb="select"], 
        .stNumberInput input {{
            background-color: {input_bg} !important;
            color: {text_primary} !important;
            border: 1.5px solid {input_border} !important;
            border-radius: 14px !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            padding: 10px 14px !important;
        }}

        .stTextInput label, 
        .stSelectbox label, 
        .stFileUploader label {{
            color: {text_primary} !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
            margin-bottom: 6px !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_top_header(title: str, subtitle: str):
    """Renders the top title and circular top-right icon buttons."""
    c_title, c_actions = st.columns([6, 1])
    
    with c_title:
        st.markdown(f"""
            <h1 style='font-size: 2.1rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;'>{title}</h1>
            <p style='color: #64748B; font-size: 0.95rem; margin-top: 4px; margin-bottom: 0;'>{subtitle}</p>
        """, unsafe_allow_html=True)

    with c_actions:
        col_dark, col_user = st.columns(2)
        with col_dark:
            st.markdown('<div class="circle-btn">', unsafe_allow_html=True)
            dark_icon = "☀️" if st.session_state.get("dark_mode", False) else "🌙"
            if st.button(dark_icon, key="global_theme_toggle", help="Toggle Theme"):
                st.session_state["dark_mode"] = not st.session_state.get("dark_mode", False)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_user:
            st.markdown('<div class="circle-btn">', unsafe_allow_html=True)
            if st.button("👤", key="global_user_profile", help="Workspace Profile"):
                st.session_state["active_page"] = "Account Access"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


def render_authenticated_sidebar():
    """Renders the minimal icon-rail with accurate Unicode icons and pinned bottom links."""
    with st.sidebar:
        current_page = st.session_state.get("active_page", "Data Ingestion")

        # Top Group
        st.container()

        # 1. Account Access
        btn_type = "primary" if current_page == "Account Access" else "secondary"
        if st.button("👤", key="nav_account", help="Account Access", type=btn_type):
            st.session_state["active_page"] = "Account Access"
            st.rerun()

        # 2. Data Ingestion
        btn_type = "primary" if current_page == "Data Ingestion" else "secondary"
        if st.button("📥", key="nav_ingestion", help="Data Ingestion", type=btn_type):
            st.session_state["active_page"] = "Data Ingestion"
            st.rerun()

        # 3. Data Preview
        btn_type = "primary" if current_page == "Data Preview" else "secondary"
        if st.button("👁️", key="nav_preview", help="Data Preview", type=btn_type):
            st.session_state["active_page"] = "Data Preview"
            st.rerun()

        # 4. Premier Dashboard
        btn_type = "primary" if current_page == "Premier Dashboard" else "secondary"
        if st.button("📊", key="nav_dashboard", help="Premier Dashboard", type=btn_type):
            st.session_state["active_page"] = "Premier Dashboard"
            st.rerun()

        # Dynamic spacer pinning Settings & Help to the bottom
        st.markdown("<div style='flex-grow: 1; min-height: 180px;'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; width: 60%; margin: 6px auto 12px auto;'>", unsafe_allow_html=True)

        # Bottom Group: Settings & Help
        if st.button("⚙️", key="nav_settings", help="Settings & Preferences"):
            st.toast("Settings opened.")

        if st.button("❓", key="nav_help", help="Documentation & Support"):
            st.toast("Help Center opened.")
            