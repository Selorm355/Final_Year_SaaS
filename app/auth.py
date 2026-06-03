import streamlit as st
import re
import user_connection

# --- Logic: Email Validator ---
def is_valid_email(email):
    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if re.match(regex, email):
        return True
    return False

# --- Logic: Password Complexity Checker ---
def is_password_strong(password):
    if len(password) < 8: return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password): return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password): return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password): return False, "Password must contain at least one number."
    if not re.search(r"[^A-Za-z0-9]", password): return False, "Password must contain at least one special symbol."
    return True, "Password is secure."

# --- SHARED CSS ---
def inject_css():
    st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] {display: none;}

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b2e 40%, #3b1f6e 100%) !important;
    }
    [data-testid="stAppViewBlockContainer"] {
        background: transparent !important;
    }

    /* Target common input elements to ensure taller fields across Streamlit versions */
    input[type="text"], input[type="password"], textarea,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    div[data-testid="stTextInput"] input {
        background-color: rgba(255, 255, 255, 0.98) !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
        border-radius: 8px !important;
        color: #111 !important;
        padding: 0.85rem 1rem !important;
        min-height: 48px !important;
        height: 48px !important;
        line-height: 1.2 !important;
        font-size: 1rem !important;
        transition: background-color 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
        box-sizing: border-box !important;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(0, 0, 0, 0.45) !important;
    }
    .stTextInput > div > div > input:focus,
    input[type="text"]:focus,
    input[type="password"]:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 3px rgba(168,85,247,0.12) !important;
        background-color: white !important;
        color: #111 !important;
    }
    .stTextInput > div > div > input:hover,
    input[type="text"]:hover,
    input[type="password"]:hover,
    .stTextArea > div > div > textarea:hover {
        background-color: rgba(255,255,255,0.98) !important;
        border-color: #a855f7 !important;
        color: #111 !important;
    }
    .stSelectbox > div > div,
    div[data-baseweb="select"] {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 8px !important;
        color: white !important;
        padding: 0.55rem 0.9rem !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        transition: background-color 120ms ease, border-color 120ms ease;
        box-sizing: border-box !important;
    }
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus-within,
    div[data-baseweb="select"]:hover {
        border-color: #a855f7 !important;
        background-color: rgba(168,85,247,0.04) !important;
    }
    div[data-testid="stFormSubmitButton"],
    div[data-testid="stButton"] {
        display: flex !important;
        justify-content: center !important;
    }
    .stFormSubmitButton > button,
    .stButton > button,
    div[data-testid="stButton"] > button {
        width: auto !important;
        min-width: 220px !important;
        max-width: 280px !important;
        padding: 0.7rem 1.4rem !important;
        background: linear-gradient(135deg, #6C63FF, #a855f7) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: transform 120ms ease, box-shadow 120ms ease, background-color 120ms ease;
        box-shadow: 0 12px 30px rgba(108, 99, 255, 0.22) !important;
        display: inline-block !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .stFormSubmitButton > button:hover,
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px) !important;
        background: linear-gradient(135deg, #7c3aed, #c084fc) !important;
    }

    .streamlit-expanderHeader,
    div[data-testid="stExpanderHeader"],
    .streamlit-expanderHeader button,
    div[data-testid="stExpanderHeader"] button,
    div[role="button"][data-testid*="stExpander"] {
        background: linear-gradient(135deg, #6C63FF, #a855f7) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: transform 120ms ease, background-color 120ms ease, box-shadow 120ms ease;
        box-shadow: 0 12px 30px rgba(108, 99, 255, 0.22) !important;
    }
    .streamlit-expanderHeader:hover,
    div[data-testid="stExpanderHeader"]:hover,
    .streamlit-expanderHeader button:hover,
    div[data-testid="stExpanderHeader"] button:hover,
    div[role="button"][data-testid*="stExpander"]:hover {
        transform: translateY(-1px) !important;
        background: linear-gradient(135deg, #7c3aed, #c084fc) !important;
    }
    .streamlit-expanderContent,
    .streamlit-expanderContent > div,
    div[data-testid="stExpander"] > div:nth-child(2) {
        background: rgba(15,23,42,0.92) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-top: none !important;
        border-radius: 0 0 16px 16px !important;
        padding: 1rem 1rem 1.2rem 1rem !important;
        color: white !important;
    }

    .stForm,
    div[data-testid="stForm"] {
        background: linear-gradient(135deg, rgba(15,23,42,0.94), rgba(30,27,46,0.96), rgba(59,31,110,0.98)) !important;
        border-radius: 24px !important;
        padding: 2rem !important;
        border: 1px solid rgba(168,85,247,0.35) !important;
        box-shadow: 0 25px 75px rgba(0,0,0,0.25) !important;
        color: white !important;
    }
    .stForm > div,
    div[data-testid="stForm"] > div {
        background: transparent !important;
    }
    .stForm label,
    div[data-testid="stForm"] label {
        color: white !important;
    }
    .back-btn {
        background: transparent;
        border: 1px solid rgba(168,85,247,0.4);
        color: rgba(255,255,255,0.6);
        border-radius: 8px;
        padding: 0.4rem 1rem;
        cursor: pointer;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }
    .back-btn:hover {
        border-color: #6C63FF;
        color: white;
    }
    .auth-form-wrapper {
        background-color: #0f172a;
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    .auth-form-card {
        background: #1e1b2e;
        border-radius: 16px;
        padding: 3rem 2.5rem;
        max-width: 480px;
        width: 100%;
        border: 1px solid rgba(168, 85, 247, 0.3);
        box-shadow: 0 0 40px rgba(108, 99, 255, 0.2);
    }
    .auth-form-card h2 {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .auth-form-card p {
        color: rgba(255,255,255,0.5);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .footer-text {
        color: rgba(255,255,255,0.3);
        font-size: 0.75rem;
        text-align: center;
        margin-top: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


def inject_auth_css():
    inject_css()


# ============================================
# SCREEN 1: LANDING PAGE
# ============================================
def show_landing_page():

    # Check for button clicks via query params
    params = st.query_params
    if params.get("action") == "login":
        st.query_params.clear()
        st.session_state["auth_screen"] = "login"
        st.rerun()
    elif params.get("action") == "register":
        st.query_params.clear()
        st.session_state["auth_screen"] = "register"
        st.rerun()

    st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding: 0 !important; max-width: 100% !important; }
    section[data-testid="stSidebar"] {display: none;}

    .landing-wrapper {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b2e 40%, #3b1f6e 100%);
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 2rem;
    }
    .landing-badge {
        background: rgba(108,99,255,0.2);
        border: 1px solid rgba(168,85,247,0.4);
        border-radius: 50px;
        padding: 0.4rem 1.4rem;
        color: #a78bfa;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 2rem;
        display: inline-block;
    }
    .landing-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: white;
        line-height: 1.15;
        margin-bottom: 1.2rem;
    }
    .landing-title span {
        background: linear-gradient(135deg, #6C63FF, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .landing-subtitle {
        color: rgba(255,255,255,0.6);
        font-size: 1.1rem;
        max-width: 520px;
        margin: 0 auto 2rem auto;
        line-height: 1.7;
    }
    .features-row {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 2.5rem;
    }
    .feature-pill {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 50px;
        padding: 0.5rem 1.2rem;
        color: rgba(255,255,255,0.75);
        font-size: 0.85rem;
    }
    .btn-row {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        margin-bottom: 2.5rem;
        margin-top: .5rem;
    }
    .btn-landing {
        display: inline-block;
        padding: 0.85rem 3rem;
        border: 2px solid white;
        border-radius: 10px;
        color: white !important;
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-decoration: none !important;
        transition: all 0.2s ease;
        cursor: pointer;
        background: transparent;
    }
    .btn-landing:hover {
        background: rgba(255,255,255,0.1);
        border-color: #a855f7;
        color: #a855f7 !important;
        text-decoration: none !important;
    }
    .landing-footer {
        color: rgba(255,255,255,0.25);
        font-size: 0.75rem;
        text-align: center;
    }
    </style>

    <div class="landing-wrapper">
        <div class="landing-badge">📊 OmniPulse Analytics Platform</div>
        <div class="landing-title">
            Your Data.<br><span>Your Insights.</span>
        </div>
        <div class="landing-subtitle">
            The all-in-one data lake platform built for Ghanaian businesses.
            Upload raw data, automate cleaning, and unlock AI-powered analytics.
        </div>
        <div class="features-row">
            <div class="feature-pill">🏭 Retail · Healthcare · Hospitality</div>
            <div class="feature-pill">⚙️ Automated Data Cleaning</div>
            <div class="feature-pill">📈 AI Forecasting</div>
            <div class="feature-pill">🔒 Secure &amp; Private</div>
        </div>
        <div class="btn-row">
            <a href="?action=login" class="btn-landing" target="_self">🔑 Log In</a>
            <a href="?action=register" class="btn-landing" target="_self">🏢 Register</a>
        </div>
        <div class="landing-footer">
            📧 support@omnipulse.com.gh &nbsp;|&nbsp; 📞 +233 20 123 4567 &nbsp;|&nbsp; 📍 Accra, Ghana
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# SCREEN 2: LOGIN PAGE
# ============================================
def show_login_page():
    inject_css()

    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

    col0, col1, col2, col3 = st.columns([0.45, 1, 4, 1])
    with col1:
        if st.button("← Back to Home"):
            st.session_state["auth_screen"] = "landing"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 1.5rem;">
            <div style="font-size:2.5rem;">🔑</div>
            <h2 style="color:white; font-weight:700; margin:0;">Welcome Back</h2>
            <p style="color:rgba(255,255,255,0.5); font-size:0.9rem;">
                Sign in to your company workspace
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            login_email = st.text_input("📧 Email Address")
            login_company = st.text_input("🏢 Company Name")
            login_password = st.text_input("🔒 Password", type="password")
            submit_login = st.form_submit_button("Log In →", use_container_width=True)

            if submit_login:
                if login_email and login_company and login_password:
                    success, user_data = user_connection.authenticate_user(
                        login_email, login_company, login_password
                    )
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["company_id"] = user_data["company_id"]
                        st.session_state["industry"] = user_data["industry"]
                        st.session_state["company_name"] = user_data["company_name"]
                        st.session_state["go_to_page"] = "2. Data Ingestion"
                        st.success(f"Welcome back, {user_data['company_name']}! 🎉")
                        st.rerun()
                    else:
                        st.error("Invalid email, company name, or password.")
                else:
                    st.error("Please fill in all fields.")

        st.markdown("""
        <div style="text-align:center; color:rgba(255,255,255,0.85); margin-top: 1rem;">
            Don't have an account? <a href="?action=register" target="_self" style="color:#a855f7; font-weight:700; text-decoration:none;">Sign up</a>
        </div>
        """, unsafe_allow_html=True)

        if "show_reset_form" not in st.session_state:
            st.session_state["show_reset_form"] = False

        if not st.session_state["show_reset_form"]:
            if st.button("🔑 Forgot Password?", key="forgot_password"):
                st.session_state["show_reset_form"] = True
                st.rerun()

        if st.session_state["show_reset_form"]:
            st.caption("Enter your details and Recovery Key to reset your password.")
            with st.form("reset_form"):
                reset_email = st.text_input("Email Address", key="res_email")
                reset_company = st.text_input("Company Name", key="res_company")
                reset_key = st.text_input("Recovery Key (e.g., A7X9-B2M4-99QQ)")
                new_password = st.text_input("New Password", type="password")
                new_password_confirm = st.text_input("Confirm New Password", type="password")
                submit_reset = st.form_submit_button("Reset Password", use_container_width=True)

                if submit_reset:
                    if not is_valid_email(reset_email):
                        st.error("Please enter a valid email address.")
                    elif new_password != new_password_confirm:
                        st.error("Passwords do not match!")
                    else:
                        is_valid, message = is_password_strong(new_password)
                        if not is_valid:
                            st.error(message)
                        else:
                            success, reset_message = user_connection.reset_password(
                                reset_email, reset_company, reset_key, new_password
                            )
                            if success:
                                st.success(reset_message)
                            else:
                                st.error(reset_message)

            if st.button("Cancel Reset", key="cancel_reset"):
                st.session_state["show_reset_form"] = False
                st.rerun()

    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)


# ============================================
# SCREEN 3: REGISTER PAGE
# ============================================
def show_register_page():
    inject_css()

    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

    col0, col1, col2, col3 = st.columns([0.45, 1, 4, 1])
    with col1:
        if st.button("← Back to Home"):
            st.session_state["auth_screen"] = "landing"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 1.5rem;">
            <div style="font-size:2.5rem;">🏢</div>
            <h2 style="color:white; font-weight:700; margin:0;">Create Your Workspace</h2>
            <p style="color:rgba(255,255,255,0.5); font-size:0.9rem;">
                Register your company to get started
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("registration_form"):
            reg_company_name = st.text_input("🏢 Company Name (e.g., Kofi Pharmacy - Osu)")
            reg_email = st.text_input("📧 Email Address")
            reg_industry = st.selectbox("🏭 Industry", ["Retail", "Hospitality", "Healthcare"])
            reg_password = st.text_input("🔒 Create Password", type="password",
                help="Must contain 8+ chars, uppercase, lowercase, number, and symbol.")
            reg_password_confirm = st.text_input("🔒 Confirm Password", type="password")
            submit_register = st.form_submit_button("Create Account →", use_container_width=True)

            if submit_register:
                if not reg_company_name or not reg_email:
                    st.error("Company Name and Email are required.")
                elif not is_valid_email(reg_email):
                    st.error("Please enter a valid email address.")
                elif reg_password != reg_password_confirm:
                    st.error("Passwords do not match!")
                else:
                    is_valid, message = is_password_strong(reg_password)
                    if not is_valid:
                        st.error(message)
                    else:
                        success, db_message, recovery_key = user_connection.register_user(
                            reg_company_name, reg_email, reg_industry, reg_password
                        )
                        if success:
                            st.success(db_message)
                            st.warning(
                                f"🚨 **CRITICAL: Save your Recovery Key!**\n\n"
                                f"This is the ONLY way to reset your password. Write it down now:\n\n"
                                f"### `{recovery_key}`"
                            )
                        else:
                            st.error(db_message)

        st.markdown("""
        <div style="text-align:center; color:rgba(255,255,255,0.85); margin-top: 1rem;">
            Already have an account? <a href="?action=login" target="_self" style="color:#a855f7; font-weight:700; text-decoration:none;">Log in</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)


# ============================================
# MAIN ROUTER — decides which screen to show
# ============================================
def show_auth_page():
    params = st.query_params
    auth_param = params.get("action", [None])[0] or params.get("auth", [None])[0]
    if auth_param in ["login", "register"]:
        if st.session_state.get("auth_screen") != auth_param:
            st.session_state["auth_screen"] = auth_param
            st.rerun()

    if "auth_screen" not in st.session_state:
        st.session_state["auth_screen"] = "landing"

    if st.session_state["auth_screen"] == "landing":
        show_landing_page()
    elif st.session_state["auth_screen"] == "login":
        show_login_page()
    elif st.session_state["auth_screen"] == "register":
        show_register_page()