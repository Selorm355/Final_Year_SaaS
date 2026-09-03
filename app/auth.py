import streamlit as st
import re
import os
import json
from cryptography.fernet import Fernet
import user_connection

# --- ENCRYPTION SETUP ---
fernet_secret = os.getenv("FERNET_KEY")
if not fernet_secret:
    st.error("🚨 CRITICAL CONFIG ERROR: FERNET_KEY is missing from environment variables.")
    st.stop()

FERNET_KEY = fernet_secret.encode()
cipher_suite = Fernet(FERNET_KEY)

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

# --- CSS INJECTOR ---
def inject_css():
    css_path = os.path.join(os.path.dirname(__file__), "auth_style.css") 
    try:
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    layout_css = """
    <style>
        /* 1. Page Canvas & Layout */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
            max-width: 1350px !important;
        }

        /* 2. Landing Page Centered Layout */
        .landing-wrapper {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            max-width: 1200px !important;
            min-height: 82vh !important;
            margin: 0 auto !important;
            width: 100% !important;
        }

        .landing-badge {
            display: inline-block !important;
            background: rgba(0, 128, 128, 0.12) !important;
            border: 1px solid #008080 !important;
            border-radius: 50px !important;
            padding: 5px 16px !important;
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            color: #006666 !important;
            margin-bottom: 2rem !important;
        }

        .landing-title {
            font-size: 4.25rem !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
            color: #2F4F4F !important;
            margin-bottom: 1.8rem !important;
        }

        .landing-title span {
            color: #008080 !important;
        }

        .landing-subtitle {
            font-size: 1.02rem !important;
            color: #5A7B7B !important;
            max-width: 600px !important;
            margin: 0 auto 1.6rem auto !important;
            line-height: 1.5 !important;
        }

        .features-row {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            flex-wrap: nowrap !important;
            gap: 12px !important;
            margin-top: 0.8rem !important;
            margin-bottom: 3.0rem !important;
            width: 100% !important;
        }

        .feature-pill.service-pill {
            background-color: #008080 !important;
            color: #FFFFFF !important;
            border: 1px solid #006666 !important;
            border-radius: 9999px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            box-shadow: 0 4px 12px rgba(0, 128, 128, 0.18) !important;
            white-space: nowrap !important;
        }

        .btn-row {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 16px !important;
            margin-bottom: 2rem !important;
        }

        .btn-landing {
            background: #FFFFFF !important;
            color: #2F4F4F !important;
            border: 1.5px solid #008080 !important;
            border-radius: 12px !important;
            padding: 10px 32px !important;
            font-weight: 700 !important;
            text-decoration: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 12px rgba(0, 128, 128, 0.08) !important;
        }

        .btn-landing:hover {
            background: #008080 !important;
            color: #FFFFFF !important;
            transform: translateY(-2px) !important;
        }

        .landing-footer {
            color: #5A7B7B !important;
            font-size: 0.82rem !important;
        }

        /* 3. Wide Container (750px) with Indented Fields (-20px each side) */
        [data-testid="stForm"] {
            max-width: 750px !important;
            margin: 0 auto !important;
            background-color: #FFFFFF !important;
            padding: 32px !important;
            border-radius: 18px !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 8px 24px rgba(0, 128, 128, 0.08) !important;
        }

        /* Reduce field length by 20px on both sides */
        [data-testid="stForm"] .stTextInput,
        [data-testid="stForm"] .stSelectbox {
            width: calc(100% - 40px) !important;
            margin-left: 20px !important;
            margin-right: 20px !important;
        }

        /* Submit Button with 20px Side Margins and 20px Margin-Top */
        [data-testid="stForm"] .stFormSubmitButton {
            width: calc(100% - 40px) !important;
            margin-left: 20px !important;
            margin-right: 20px !important;
            margin-top: 20px !important;
        }

        /* Center-Aligned Field Labels */
        [data-testid="stForm"] .stTextInput label,
        [data-testid="stForm"] .stSelectbox label {
            display: flex !important;
            justify-content: center !important;
            text-align: center !important;
            width: 100% !important;
            color: #2F4F4F !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            margin-bottom: 6px !important;
        }

        [data-testid="stForm"] .stTextInput label p,
        [data-testid="stForm"] .stSelectbox label p {
            text-align: center !important;
            width: 100% !important;
        }

        /* Center Typed Text & Placeholders */
        [data-testid="stForm"] .stTextInput input {
            text-align: center !important;
            border-radius: 12px !important;
            border: 1.5px solid #CBD5E1 !important;
            padding: 10px 42px 10px 42px !important;
            font-size: 1.00rem !important;
            color: #2F4F4F !important;
            height: 45px !important;
        }

        [data-testid="stForm"] .stTextInput input::placeholder {
            text-align: center !important;
            color: #94A3B8 !important;
        }

        /* Dropdown selection field styling */
        [data-testid="stForm"] .stSelectbox div[data-baseweb="select"] {
            border-radius: 12px !important;
            border: 1.5px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
            height: 45px !important;
            min-height: 45px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: none !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stForm"] .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: #008080 !important;
            box-shadow: 0 0 0 1px #008080 !important;
        }

        [data-testid="stForm"] .stSelectbox div[data-baseweb="select"] > div:first-child {
            background-color: transparent !important;
            border: none !important;
            padding: 0 14px 0 42px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
            height: 100% !important;
            cursor: pointer !important;
        }

        [data-testid="stForm"] .stSelectbox input {
            text-align: center !important;
            cursor: pointer !important;
            caret-color: transparent !important;
            font-size: 1.00rem !important;
            color: #2F4F4F !important;
        }

        [data-testid="stForm"] .stSelectbox [data-baseweb="select"] div {
            text-align: center !important;
            justify-content: center !important;
            font-size: 1.00rem !important;
            color: #2F4F4F !important;
        }

        [data-testid="stForm"] .stSelectbox input::placeholder,
        [data-testid="stForm"] .stSelectbox [data-baseweb="select"] div[class*="placeholder"] {
            text-align: center !important;
            color: #94A3B8 !important;
            font-size: 1.00rem !important;
        }

        [data-testid="stForm"] .stSelectbox [data-baseweb="select"] svg {
            fill: #2F4F4F !important;
            margin-right: 8px !important;
            cursor: pointer !important;
        }

        [data-testid="stForm"] div[data-baseweb="input"] button {
            margin-left: auto !important;
            margin-right: 6px !important;
        }

        /* 4. Control "Press Enter to Submit" Instructions */
        [data-testid="stForm"] [data-testid="InputInstructions"] {
            display: none !important;
        }

        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Enter your password"]) [data-testid="InputInstructions"],
        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Re-enter password"]) [data-testid="InputInstructions"],
        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Confirm new password"]) [data-testid="InputInstructions"] {
            display: flex !important;
            justify-content: flex-end !important;
            text-align: right !important;
            width: 100% !important;
            margin-top: 4px !important;
            padding-right: 4px !important;
        }

        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Enter your password"]) [data-testid="InputInstructions"] *,
        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Re-enter password"]) [data-testid="InputInstructions"] *,
        [data-testid="stForm"] [data-testid="stTextInput"]:has(input[placeholder="Confirm new password"]) [data-testid="InputInstructions"] * {
            text-align: right !important;
            color: #5A7B7B !important;
            font-size: 0.78rem !important;
        }
    </style>
    """
    st.markdown(layout_css, unsafe_allow_html=True)

# ============================================
# SCREEN 1: LANDING PAGE
# ============================================
def show_landing_page():
    inject_css()
    params = st.query_params
    action = params.get("action") or params.get("auth")
    if isinstance(action, list): action = action[0] if action else None

    if action in ["login", "register", "reset"]:
        if "action" in st.query_params: del st.query_params["action"]
        if "auth" in st.query_params: del st.query_params["auth"]
        st.session_state["auth_screen"] = action
        st.rerun()

    st.markdown("""
    <div class="landing-wrapper">
        <div class="landing-badge">📊 OmniPulse Analytics Platform</div>
        <div class="landing-title">
            Your Data.<br><span>Your Insights.</span>
        </div>
        <div class="landing-subtitle">
            The all-in-one data lake platform built for Ghanaian businesses.<br>
            Upload raw data, automate cleaning, and unlock AI-powered analytics.
        </div>
        <div class="features-row">
            <div class="feature-pill service-pill">🏭 Retail · Healthcare · Hospitality</div>
            <div class="feature-pill service-pill">⚙️ Automated Data Cleaning</div>
            <div class="feature-pill service-pill">📈 AI Forecasting</div>
            <div class="feature-pill service-pill">🔒 Secure &amp; Private</div>
        </div>
        <div class="btn-row">
            <a href="?action=login" class="btn-landing" target="_self">🔑 Log In</a>
            <a href="?action=register" class="btn-landing" target="_self">🏢 Register</a>
        </div>
        <div class="landing-footer">
            📧 support@omnipulse.com.gh &nbsp;|&nbsp; 📞 +233 55 571 010 &nbsp;|&nbsp; 📍 Accra, Ghana
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# SCREEN 2: LOGIN PAGE
# ============================================
def show_login_page():
    inject_css()
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    left_col, center_col, right_col = st.columns([1, 4, 1])
    with left_col:
        if st.button("← Back to Home"):
            st.query_params.clear()
            st.session_state["auth_screen"] = "landing"
            st.rerun()

    with center_col:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.2rem;">
            <div style="font-size: 2.3rem; margin-bottom: 0.3rem;">🔑</div>
            <h2 style="color: #2F4F4F; font-weight: 700; margin: 0; font-size: 3.0rem;">Welcome Back</h2>
            <p style="color: #5A7B7B; font-size: 0.88rem; margin-top: 0.3rem; margin-bottom: 1rem;">
                Sign in to your company workspace
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            login_email = st.text_input("📧 Email Address", placeholder="email@gmail.com")
            login_company = st.text_input("🏢 Company Name", placeholder="Enter registered business name")
            login_password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Log In →", use_container_width=True)

            if submit_login:
                if login_email and login_company and login_password:
                    clean_email = login_email.strip().lower()
                    clean_company = login_company.strip()
                    
                    success, user_data = user_connection.authenticate_user(
                        clean_email, clean_company, login_password
                    )
                    if success:
                        st.session_state["logged_in"] = True
                        st.session_state["company_id"] = user_data["company_id"]
                        st.session_state["industry"] = user_data["industry"]
                        st.session_state["company_name"] = user_data["company_name"]
                        
                        token_dict = {
                            "company_id": user_data["company_id"],
                            "industry": user_data["industry"],
                            "company_name": user_data["company_name"]
                        }
                        encrypted_token = cipher_suite.encrypt(json.dumps(token_dict).encode()).decode()
                        st.query_params["token"] = encrypted_token
                        
                        st.session_state["go_to_page"] = "2. Data Ingestion"
                        st.rerun()
                    else:
                        st.error("Invalid email, company name, or password.")
                else:
                    st.error("Please fill in all fields.")

        # Teal Link for Forgot Password and Sign Up Navigation
        st.markdown("""
        <div style="text-align: center; margin-top: 1.2rem; margin-bottom: 0.6rem;">
            <a href="?action=reset" target="_self" style="color: #008080; font-weight: 700; text-decoration: none; font-size: 0.92rem;">
                🔑 Forgot Password?
            </a>
        </div>
        <div style="text-align: center; color: #2F4F4F; font-size: 0.9rem;">
            Don't have an account? <a href="?action=register" target="_self" style="color: #008080; font-weight: 700; text-decoration: none;">Sign up</a>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# SCREEN 3: REGISTER PAGE
# ============================================
def show_register_page():
    inject_css()
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    left_col, center_col, right_col = st.columns([1, 4, 1])
    with left_col:
        if st.button("← Back to Home"):
            st.query_params.clear()
            st.session_state["auth_screen"] = "landing"
            st.rerun()

    with center_col:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.2rem;">
            <div style="font-size: 2.3rem; margin-bottom: 0.3rem;">🏢</div>
            <h2 style="color: #2F4F4F; font-weight: 700; margin: 0; font-size: 3.0rem;">Create Your Workspace</h2>
            <p style="color: #5A7B7B; font-size: 0.88rem; margin-top: 0.3rem; margin-bottom: 1rem;">
                Register your company to get started
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("registration_form"):
            reg_company_name = st.text_input("🏢 Company Name", placeholder="e.g., Kofi Pharmacy - Osu")
            reg_email = st.text_input("📧 Email Address", placeholder="email@gmail.com")
            reg_industry = st.selectbox(
                "🏭 Industry", 
                ["Retail", "Hospitality", "Healthcare"],
                index=None,
                placeholder="Select prefered industry"
            )
            reg_password = st.text_input("🔒 Create Password", type="password", placeholder="At least 8 characters")
            reg_password_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password")
            submit_register = st.form_submit_button("Create Account →", use_container_width=True)

            if submit_register:
                clean_reg_company_name = reg_company_name.strip()
                clean_reg_email = reg_email.strip().lower()
                
                if not clean_reg_company_name or not clean_reg_email or not reg_industry: 
                    st.error("Company Name, Email, and Industry are required.")
                elif not is_valid_email(clean_reg_email): 
                    st.error("Please enter a valid email address.")
                elif reg_password != reg_password_confirm: 
                    st.error("Passwords do not match!")
                else:
                    is_valid, message = is_password_strong(reg_password)
                    if not is_valid: 
                        st.error(message)
                    else:
                        success, db_message, recovery_key = user_connection.register_user(
                            clean_reg_company_name, clean_reg_email, reg_industry, reg_password
                        )
                        if success:
                            st.success(db_message)
                            st.warning(f"🚨 **CRITICAL: Save your Recovery Key!**\n\n### `{recovery_key}`")
                        else:
                            st.error(db_message)

        st.markdown("""
        <div style="text-align: center; color: #2F4F4F; margin-top: 1rem; font-size: 0.9rem;">
            Already have an account? <a href="?action=login" target="_self" style="color: #008080; font-weight: 700; text-decoration: none;">Log in</a>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# SCREEN 4: FORGOT / RESET PASSWORD PAGE
# ============================================
def show_reset_password_page():
    inject_css()
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    left_col, center_col, right_col = st.columns([1, 4, 1])
    with left_col:
        if st.button("← Back to Login"):
            st.query_params.clear()
            st.session_state["auth_screen"] = "login"
            st.rerun()

    with center_col:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.2rem;">
            <div style="font-size: 2.3rem; margin-bottom: 0.3rem;">🔄</div>
            <h2 style="color: #2F4F4F; font-weight: 700; margin: 0; font-size: 3.0rem;">Reset Password</h2>
            <p style="color: #5A7B7B; font-size: 0.88rem; margin-top: 0.3rem; margin-bottom: 1rem;">
                Enter your company credentials and Recovery Key to reset your password
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("reset_password_page_form"):
            reset_email = st.text_input("📧 Email Address", placeholder="name@gmail.com")
            reset_company = st.text_input("🏢 Company Name", placeholder="Enter registered business name")
            reset_key = st.text_input("🔑 Recovery Key", placeholder="Paste recovery key")
            new_password = st.text_input("🔒 New Password", type="password", placeholder="Enter new password")
            new_password_confirm = st.text_input("🔒 Confirm New Password", type="password", placeholder="Confirm new password")
            submit_reset = st.form_submit_button("Reset Password →", use_container_width=True)

            if submit_reset:
                clean_reset_email = reset_email.strip().lower()
                clean_reset_company = reset_company.strip()
                clean_key = reset_key.strip()
                
                if not is_valid_email(clean_reset_email): 
                    st.error("Please enter a valid email address.")
                elif not clean_reset_company or not clean_key:
                    st.error("Company name and Recovery Key are required.")
                elif new_password != new_password_confirm: 
                    st.error("Passwords do not match!")
                else:
                    is_valid, message = is_password_strong(new_password)
                    if not is_valid: 
                        st.error(message)
                    else:
                        success, reset_message = user_connection.reset_password(
                            clean_reset_email, clean_reset_company, clean_key, new_password
                        )
                        if success: 
                            st.success(reset_message)
                            st.info("You can now log in with your updated password.")
                        else: 
                            st.error(reset_message)

        st.markdown("""
        <div style="text-align: center; color: #2F4F4F; margin-top: 1rem; font-size: 0.9rem;">
            Remember your credentials? <a href="?action=login" target="_self" style="color: #008080; font-weight: 700; text-decoration: none;">Back to login</a>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# SCREEN 5: LOGGED IN PROFILE (Redesigned SaaS Workspace)
# ============================================
def show_user_profile():
    inject_css()
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 2.2, 1.5])
    with col2:
        company_name = st.session_state.get('company_name', 'Your Workspace')
        industry = st.session_state.get('industry', 'Enterprise').capitalize()
        
        industry_icon = "🛒" if "retail" in industry.lower() else ("🏥" if "health" in industry.lower() else ("🏨" if "hospit" in industry.lower() else "🏢"))
        
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 2rem; padding: 2rem; background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 18px; box-shadow: 0 4px 20px rgba(0, 128, 128, 0.12);">
            <div style="font-size:3.2rem; margin-bottom: 0.5rem;">{industry_icon}</div>
            <h1 style="color:#2F4F4F; font-weight:700; margin:0; font-size: 2rem;">{company_name}</h1>
            <div style="display: inline-block; margin-top: 0.8rem; padding: 0.3rem 1rem; background: rgba(0, 128, 128, 0.12); border: 1px solid #008080; border-radius: 50px; color: #006666; font-size: 0.88rem; font-weight: 600;">
                ✨ {industry} Analytics Workspace
            </div>
            <p style="color:#5A7B7B; font-size:0.92rem; margin-top: 1.2rem; margin-bottom: 0;">
                Your data pipelines, AI forecasting models, and cleaning engines are active and ready.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Go to Data Ingestion", use_container_width=True):
                st.session_state["go_to_page"] = "2. Data Ingestion"
                st.rerun()
        with col_btn2:
            if st.button("Log Out of OmniPulse", use_container_width=True):
                st.query_params.clear()
                st.session_state.clear()
                st.rerun()

# ============================================
# MAIN ROUTER
# ============================================
def show_auth_page(): 
    if st.session_state.get("logged_in"):
        show_user_profile() 
        return

    params = st.query_params
    auth_param = params.get("action") or params.get("auth")
    if isinstance(auth_param, list):
        auth_param = auth_param[0] if auth_param else None

    if auth_param in ["login", "register", "reset"]:
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
    elif st.session_state["auth_screen"] == "reset":
        show_reset_password_page()