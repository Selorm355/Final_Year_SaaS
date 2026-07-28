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
        st.warning("⚠️ CSS file not found. Ensure 'auth_style.css' is in the same directory.") 

# ============================================
# SCREEN 1: LANDING PAGE
# ============================================
def show_landing_page():
    inject_css()
    params = st.query_params
    if params.get("action") == "login":
        if "action" in st.query_params: del st.query_params["action"]
        st.session_state["auth_screen"] = "login"
        st.rerun()
    elif params.get("action") == "register":
        if "action" in st.query_params: del st.query_params["action"]
        st.session_state["auth_screen"] = "register"
        st.rerun()

    st.markdown("""
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

        st.markdown("""
        <div style="text-align:center; color:rgba(255,255,255,0.85); margin-top: 1rem;">
            Don't have an account? <a href="?action=register" target="_self" style="color:#a855f7; font-weight:700; text-decoration:none;">Sign up</a>
        </div>
        """, unsafe_allow_html=True)

        if "show_reset_form" not in st.session_state: st.session_state["show_reset_form"] = False
        if not st.session_state["show_reset_form"]:
            if st.button("🔑 Forgot Password?", key="forgot_password"):
                st.session_state["show_reset_form"] = True
                st.rerun()
        if st.session_state["show_reset_form"]:
            st.caption("Enter your details and Recovery Key to reset your password.")
            with st.form("reset_form"):
                reset_email = st.text_input("Email Address", key="res_email")
                reset_company = st.text_input("Company Name", key="res_company")
                reset_key = st.text_input("Recovery Key")
                new_password = st.text_input("New Password", type="password")
                new_password_confirm = st.text_input("Confirm New Password", type="password")
                submit_reset = st.form_submit_button("Reset Password", use_container_width=True)

                if submit_reset:
                    if not is_valid_email(reset_email): st.error("Please enter a valid email address.")
                    elif new_password != new_password_confirm: st.error("Passwords do not match!")
                    else:
                        is_valid, message = is_password_strong(new_password)
                        if not is_valid: st.error(message)
                        else:
                            success, reset_message = user_connection.reset_password(
                                reset_email, reset_company, reset_key, new_password
                            )
                            if success: st.success(reset_message)
                            else: st.error(reset_message)
            if st.button("Cancel Reset", key="cancel_reset"):
                st.session_state["show_reset_form"] = False
                st.rerun()

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
            reg_password = st.text_input("🔒 Create Password", type="password")
            reg_password_confirm = st.text_input("🔒 Confirm Password", type="password")
            submit_register = st.form_submit_button("Create Account →", use_container_width=True)

            if submit_register:
                if not reg_company_name or not reg_email: st.error("Company Name and Email are required.")
                elif not is_valid_email(reg_email): st.error("Please enter a valid email address.")
                elif reg_password != reg_password_confirm: st.error("Passwords do not match!")
                else:
                    is_valid, message = is_password_strong(reg_password)
                    if not is_valid: st.error(message)
                    else:
                        success, db_message, recovery_key = user_connection.register_user(
                            reg_company_name, reg_email, reg_industry, reg_password
                        )
                        if success:
                            st.success(db_message)
                            st.warning(f"🚨 **CRITICAL: Save your Recovery Key!**\n\n### `{recovery_key}`")
                        else:
                            st.error(db_message)

        st.markdown("""
        <div style="text-align:center; color:rgba(255,255,255,0.85); margin-top: 1rem;">
            Already have an account? <a href="?action=login" target="_self" style="color:#a855f7; font-weight:700; text-decoration:none;">Log in</a>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# SCREEN 4: LOGGED IN PROFILE (Redesigned SaaS Workspace)
# ============================================
def show_user_profile():
    inject_css()
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        company_name = st.session_state.get('company_name', 'Your Workspace')
        industry = st.session_state.get('industry', 'Enterprise').capitalize()
        
        # Pick an icon depending on their industry
        industry_icon = "🛒" if "retail" in industry.lower() else ("🏥" if "health" in industry.lower() else ("🏨" if "hospit" in industry.lower() else "🏢"))
        
        # Welcoming, user-friendly SaaS Header
        st.markdown(f"""
        <div style="text-align:center; margin-bottom: 2rem; padding: 2rem; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);">
            <div style="font-size:3.5rem; margin-bottom: 0.5rem;">{industry_icon}</div>
            <h1 style="color:white; font-weight:700; margin:0; font-size: 2.2rem;">{company_name}</h1>
            <div style="display: inline-block; margin-top: 0.8rem; padding: 0.3rem 1rem; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4); border-radius: 50px; color: #d8b4fe; font-size: 0.9rem; font-weight: 600;">
                ✨ {industry} Analytics Workspace
            </div>
            <p style="color:rgba(255,255,255,0.6); font-size:0.95rem; margin-top: 1.2rem; margin-bottom: 0;">
                Your data pipelines, AI forecasting models, and cleaning engines are active and ready.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Action Buttons
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