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
    
    # THE FIX: [^A-Za-z0-9] means "Match anything that is NOT a standard letter or number"
    if not re.search(r"[^A-Za-z0-9]", password): return False, "Password must contain at least one special symbol."
    
    return True, "Password is secure."

# --- UI: The Stacked Authentication Page ---
def show_auth_page():
    st.title("🔐 Account Access")
    st.write("Welcome to OmniPulse! Please register your company or log in below.")
    
    # -----------------------------------------
    # TOP SECTION: REGISTRATION
    # -----------------------------------------
    st.header("🏢 Register New Company Workspace")
    
    with st.form("registration_form"):
        reg_company_name = st.text_input("Company Name (e.g., Kofi Pharmacy - Osu)")
        reg_email = st.text_input("Email Address")
        reg_industry = st.selectbox("Industry", ["Retail", "Hospitality", "Healthcare"])
        reg_password = st.text_input("Create Password", type="password", help="Must contain 8+ chars, Upper, Lower, Number, and Symbol.")
        reg_password_confirm = st.text_input("Confirm Password", type="password")
        
        submit_register = st.form_submit_button("Register Account")
        
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
                        st.warning(f"🚨 **CRITICAL: Save your Recovery Key!** 🚨\n\nIf you forget your password, this is the ONLY way to reset it. Write it down now:\n\n### `{recovery_key}`")
                    else:
                        st.error(db_message) 

    st.divider() 

    # -----------------------------------------
    # BOTTOM SECTION: LOGIN (Workspace Update)
    # -----------------------------------------
    st.header("🔑 Log In")
    
    with st.form("login_form"):
        login_email = st.text_input("Email Address")
        login_company = st.text_input("Company Name")
        login_password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Log In")
        
        if submit_login:
            if login_email and login_company and login_password:
                success, user_data = user_connection.authenticate_user(login_email, login_company, login_password)
                if success:
                    st.session_state["logged_in"] = True
                    st.session_state["company_id"] = user_data["company_id"]
                    st.session_state["industry"] = user_data["industry"]
                    st.session_state["company_name"] = user_data["company_name"]
                    st.success(f"Welcome back, {user_data['company_name']}! You can now navigate to Data Ingestion.")
                else:
                    st.error("Invalid email, company name, or password.")
            else:
                st.error("Please enter your email, company name, and password.")

    # -----------------------------------------
    # PASSWORD RESET OVERRIDE (Workspace Update)
    # -----------------------------------------
    st.write("") 
    with st.expander("Forgot or Change Password?"):
        st.info("Enter your Email, Company Name, and your 12-character Recovery Key to create a new password.")
        with st.form("reset_form"):
            reset_email = st.text_input("Email Address", key="res_email")
            reset_company = st.text_input("Company Name", key="res_company")
            reset_key = st.text_input("Recovery Key (e.g., A7X9-B2M4-99QQ)")
            new_password = st.text_input("New Password", type="password")
            new_password_confirm = st.text_input("Confirm New Password", type="password")
            
            submit_reset = st.form_submit_button("Reset Password")
            
            if submit_reset:
                if not is_valid_email(reset_email):
                    st.error("Please enter a valid email address.")
                elif new_password != new_password_confirm:
                    st.error("New passwords do not match!")
                else:
                    is_valid, message = is_password_strong(new_password)
                    if not is_valid:
                        st.error(message)
                    else:
                        success, reset_message = user_connection.reset_password(reset_email, reset_company, reset_key, new_password)
                        if success:
                            st.success(reset_message)
                        else:
                            st.error(reset_message)

    # -----------------------------------------
    # FOOTER: SUPPORT & CONTACT
    # -----------------------------------------
    st.divider()
    st.caption("🏢 **OmniPulse Analytics Support**")
    st.caption("Lost your Recovery Key? Please contact our technical team for manual identity verification and account recovery.")
    st.caption("📧 support@omnipulse.com.gh | 📞 +233 20 123 4567 | 📍 Accra, Ghana")