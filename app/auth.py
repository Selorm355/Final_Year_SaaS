import streamlit as st
import re

# --- Logic: Password Complexity Checker ---
def is_password_strong(password):
    """
    Checks if password has at least:
    8 characters, 1 uppercase, 1 lowercase, 1 number, and 1 special symbol.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special symbol."
    
    return True, "Password is secure."

# --- UI: The Stacked Authentication Page ---
def show_auth_page():
    st.title("🔐 Account Access")
    st.write("Welcome to OmniPulse! Please register your company or log in below.")
    
    # -----------------------------------------
    # TOP SECTION: REGISTRATION
    # -----------------------------------------
    st.header("🏢 Register New Company")
    
    with st.form("registration_form"):
        reg_company_name = st.text_input("Company Name")
        reg_email = st.text_input("Email Address")
        reg_industry = st.selectbox("Industry", ["Retail", "Telecom", "Healthcare"])
        reg_password = st.text_input("Create Password", type="password", help="Must contain 8+ chars, Upper, Lower, Number, and Symbol.")
        reg_password_confirm = st.text_input("Confirm Password", type="password")
        
        submit_register = st.form_submit_button("Register Account")
        
        if submit_register:
            if reg_password != reg_password_confirm:
                st.error("Passwords do not match!")
            else:
                is_valid, message = is_password_strong(reg_password)
                if not is_valid:
                    st.error(message)
                else:
                    # TODO: Database insertion will go here later
                    st.success(f"Success! {reg_company_name} registered under {reg_industry}. (Database linking coming soon)")

    st.divider() # Creates a clean visual line between the forms

    # -----------------------------------------
    # BOTTOM SECTION: LOGIN
    # -----------------------------------------
    st.header("🔑 Log In")
    
    with st.form("login_form"):
        login_email = st.text_input("Email Address")
        login_password = st.text_input("Password", type="password")
        
        submit_login = st.form_submit_button("Log In")
        
        if submit_login:
            # TODO: Database verification will go here later
            # For now, we simulate a successful login to test Session State
            if login_email and login_password:
                st.session_state["logged_in"] = True
                st.session_state["company_id"] = "DEMO-101" # Placeholder
                st.session_state["industry"] = "Retail" # Placeholder
                st.success("Login successful! You can now navigate to Data Ingestion.")
            else:
                st.error("Please enter both email and password.")