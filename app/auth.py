import streamlit as st
import re
import user_connection  # Imports your new database manager

# --- Logic: Email Validator ---
def is_valid_email(email):
    """Checks if the email follows a standard format (e.g., name@domain.com)"""
    # This Regex looks for characters, an @ symbol, characters, a dot, and characters
    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if re.match(regex, email):
        return True
    return False

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
            # 1. Check if email is a real format
            if not is_valid_email(reg_email):
                st.error("Please enter a valid email address.")
            # 2. Check if passwords match
            elif reg_password != reg_password_confirm:
                st.error("Passwords do not match!")
            else:
                # 3. Check if password is secure
                is_valid, message = is_password_strong(reg_password)
                if not is_valid:
                    st.error(message)
                else:
                    # 4. Send to Database!
                    success, db_message = user_connection.register_user(
                        reg_company_name, reg_email, reg_industry, reg_password
                    )
                    
                    if success:
                        st.success(db_message)
                    else:
                        st.error(db_message) # Shows error if email already exists

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
            if login_email and login_password:
                # 1. Verify with Database!
                success, user_data = user_connection.authenticate_user(login_email, login_password)
                
                if success:
                    # 2. Save their real data into the Session Memory
                    st.session_state["logged_in"] = True
                    st.session_state["company_id"] = user_data["company_id"]
                    st.session_state["industry"] = user_data["industry"]
                    st.session_state["company_name"] = user_data["company_name"]
                    
                    st.success(f"Welcome back, {user_data['company_name']}! You can now navigate to Data Ingestion.")
                else:
                    st.error("Invalid email or password.")
            else:
                st.error("Please enter both email and password.")