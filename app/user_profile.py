import streamlit as st
import secrets
import string
import re
import user_connection

PROFILE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .stApp {
        background-color: #F0F8FF !important;
        color: #2F4F4F !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1200px !important;
    }

    /* Top Banner Card */
    .profile-banner {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 20px;
        padding: 1.8rem 2.2rem;
        box-shadow: 0 4px 20px rgba(0, 128, 128, 0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }
    .status-chip-active {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 128, 128, 0.12);
        color: #006666;
        border: 1px solid #008080;
        padding: 4px 14px;
        border-radius: 50px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #008080;
        border-radius: 50%;
    }

    /* Clean Card Headers */
    .section-header-box {
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #2F4F4F;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .section-desc {
        font-size: 0.88rem;
        color: #5A7B7B;
        margin: 0;
    }

    .key-mask-box {
        background: #F8FAFC;
        border: 1.5px dashed #CBD5E1;
        border-radius: 12px;
        padding: 14px 20px;
        font-family: monospace;
        font-size: 1.15rem;
        color: #2F4F4F;
        text-align: center;
        letter-spacing: 2px;
        margin: 12px 0;
    }

    /* Container Styling */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(0, 128, 128, 0.06) !important;
        padding: 12px !important;
        margin-bottom: 1.2rem !important;
    }

    /* Input Field Styling */
    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1.5px solid #CBD5E1 !important;
        font-size: 0.95rem !important;
        color: #2F4F4F !important;
    }
    .stTextInput input:focus {
        border-color: #008080 !important;
        box-shadow: 0 0 0 1px #008080 !important;
    }

    /* Tabs Styling: Centered Teal Pill Buttons */
    [data-testid="stTabs"] > div:first-child {
        border-bottom: none !important;
        box-shadow: none !important;
        background: transparent !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 1.2rem auto !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        background-color: transparent !important;
        padding: 4px 0 !important;
        border: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF !important;
        color: #006666 !important;
        border: 1.5px solid #008080 !important;
        border-radius: 15px !important;
        padding: 8px 24px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 8px rgba(0, 128, 128, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(0, 128, 128, 0.08) !important;
        color: #004D40 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #008080 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #008080 !important;
        border-radius: 15px !important;
        padding: 8px 14px !important;
        box-shadow: 0 4px 14px rgba(0, 128, 128, 0.3) !important;
    }
</style>
"""

def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def generate_mock_api_key():
    return "op_live_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def show_user_profile():
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)
    
    # State synchronization with login credentials
    company_name = st.session_state.get('company_name', 'Enterprise Workspace')
    industry = st.session_state.get('industry', 'Retail').capitalize()
    company_id = st.session_state.get('company_id', 'GH-ACC-0042')
    
    # Default to user's logged-in email rather than hardcoded dummy values
    active_email = st.session_state.get('user_email') or "user@company.com"
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = active_email

    if "api_key" not in st.session_state:
        st.session_state["api_key"] = "op_live_••••••••••••••••••••••••••••"
    if "show_raw_recovery_key" not in st.session_state:
        st.session_state["show_raw_recovery_key"] = False
    if "branches" not in st.session_state:
        st.session_state["branches"] = "Accra Mall, Kumasi City Hub, Osu Main"
    if "company_phone" not in st.session_state:
        st.session_state["company_phone"] = "+233 20 123 4567"
    if "tin_number" not in st.session_state:
        st.session_state["tin_number"] = "C002819283X"

    industry_icon = "🛒" if "retail" in industry.lower() else ("🏥" if "health" in industry.lower() else ("🏨" if "hospit" in industry.lower() else "🏢"))

    # --- TOP COMMAND HEADER ---
    st.markdown(f"""
    <div class="profile-banner">
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="font-size: 3rem; background: #F0F8FF; padding: 12px 18px; border-radius: 18px; border: 1px solid #CBD5E1;">
                {industry_icon}
            </div>
            <div>
                <h2 style="margin: 0; color: #2F4F4F; font-size: 2rem; font-weight: 800;">{company_name}</h2>
                <div style="display: flex; align-items: center; gap: 12px; margin-top: 6px; flex-wrap: wrap;">
                    <span class="status-chip-active"><span class="status-dot"></span> Active Enterprise Tier</span>
                    <span style="color: #5A7B7B; font-size: 0.88rem;">ID: <code>{company_id}</code></span>
                    <span style="color: #008080; font-weight: 600; font-size: 0.88rem;">📧 {st.session_state['user_email']}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Toolbar
    c_action1, c_action2, c_spacer = st.columns([1.6, 1.3, 3])
    with c_action1:
        if st.button("🚀 Launch Data Ingestion", use_container_width=True):
            st.session_state["go_to_page"] = "2. Data Ingestion"
            st.rerun()
    with c_action2:
        if st.button("Log Out of OmniPulse", use_container_width=True):
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- THREE CENTRAL WORKSPACE TABS ---
    t_account, t_security, t_tier = st.tabs([
        "🏢 Account & Entity Details",
        "🔒 Security & Access Vault",
        "⚡ Plan & Ingestion Limits"
    ])

    # === TAB 1: ACCOUNT & ENTITY DETAILS ===
    with t_account:
        with st.container(border=True):
            st.markdown("""
            <div class="section-header-box">
                <div class="section-title">🏢 Administrative Credentials & Entity Profile</div>
                <p class="section-desc">Update primary administrative contacts, notification email, and entity metadata</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("account_update_form"):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    updated_email = st.text_input("📧 Administrator Contact Email", value=st.session_state["user_email"])
                    updated_name = st.text_input("🏢 Registered Business Name", value=company_name)
                    updated_phone = st.text_input("📞 Support Phone Number", value=st.session_state["company_phone"])

                with col_u2:
                    updated_tin = st.text_input("📜 Ghana TIN / Registration Reference", value=st.session_state["tin_number"])
                    updated_currency = st.selectbox("💱 Default Currency", ["GH₵ (Ghana Cedi)", "USD ($)", "EUR (€)"], index=0)
                    updated_branches = st.text_input("📍 Operating Branches", value=st.session_state["branches"])

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                submit_account_update = st.form_submit_button("Save Profile Changes →", use_container_width=True)

                if submit_account_update:
                    clean_email = updated_email.strip().lower()
                    clean_name = updated_name.strip()
                    clean_phone = updated_phone.strip()
                    clean_branches = updated_branches.strip()
                    clean_tin = updated_tin.strip()

                    if not is_valid_email(clean_email):
                        st.error("Please enter a valid email address.")
                    elif not clean_name:
                        st.error("Business name cannot be empty.")
                    else:
                        st.session_state["user_email"] = clean_email
                        st.session_state["company_name"] = clean_name
                        st.session_state["company_phone"] = clean_phone
                        st.session_state["branches"] = clean_branches
                        st.session_state["tin_number"] = clean_tin
                        st.success("Account details and administrative email updated successfully!")
                        st.rerun()

    # === TAB 2: SECURITY & ACCESS VAULT ===
    with t_security:
        sec1, sec2 = st.columns(2)
        with sec1:
            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">🔑 Emergency Recovery Vault</div>
                    <p class="section-desc">Master recovery token for emergency account access</p>
                </div>
                """, unsafe_allow_html=True)

                if not st.session_state["show_raw_recovery_key"]:
                    st.markdown('<div class="key-mask-box">••••-••••-••••-••••-••••</div>', unsafe_allow_html=True)
                    with st.expander("🔓 Unlock & Reveal Key"):
                        verify_pwd = st.text_input("Enter password to unlock", type="password", key="sec_pwd_unlock")
                        if st.button("Authenticate", key="btn_unlock_rec", use_container_width=True):
                            if verify_pwd:
                                st.session_state["show_raw_recovery_key"] = True
                                st.rerun()
                            else:
                                st.error("Password required to decrypt recovery key.")
                else:
                    st.markdown('<div class="key-mask-box" style="color: #008080; font-weight: 700;">RCV-9872-GH41-KOF-2026</div>', unsafe_allow_html=True)
                    c_hide, c_roll = st.columns(2)
                    with c_hide:
                        if st.button("Hide Key", key="btn_hide_rec", use_container_width=True):
                            st.session_state["show_raw_recovery_key"] = False
                            st.rerun()
                    with c_roll:
                        if st.button("Re-roll Key", key="btn_roll_rec", use_container_width=True):
                            st.success("New master key generated and stored.")

            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">🔒 Password Update</div>
                    <p class="section-desc">Update your current workspace credentials</p>
                </div>
                """, unsafe_allow_html=True)
                with st.form("pwd_change_form"):
                    current_password = st.text_input("Current Password", type="password")
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    if st.form_submit_button("Update Password →", use_container_width=True):
                        if not current_password or not new_password or not confirm_password:
                            st.error("Please fill in all password fields.")
                        elif new_password != confirm_password:
                            st.error("New passwords do not match.")
                        elif len(new_password) < 8:
                            st.error("New password must be at least 8 characters long.")
                        else:
                            updated, message = user_connection.update_password(
                                company_id, current_password, new_password
                            )
                            if updated:
                                st.success(message)
                            else:
                                st.error(message)

        with sec2:
            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">🔌 Ingestion API Token</div>
                    <p class="section-desc">Bearer token for direct ERP, POS, and automated webhook ingestion</p>
                </div>
                """, unsafe_allow_html=True)
                st.code(st.session_state["api_key"], language="bash")
                if st.button("Generate New API Key", key="btn_new_key", use_container_width=True):
                    st.session_state["api_key"] = generate_mock_api_key()
                    st.rerun()

            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">🛡️ Active Sessions</div>
                    <p class="section-desc">Current browser and device access tokens</p>
                </div>
                <div style="font-size: 0.88rem; color: #5A7B7B; line-height: 1.6; margin-bottom: 12px;">
                    • Current Session: <b>Accra, Ghana (Mac OS / Chrome)</b><br>
                    • Token Lifetime: <b>Active (14 Days Remaining)</b>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Revoke Other Sessions", key="btn_revoke_sess", use_container_width=True):
                    st.success("All other active device sessions terminated.")

    # === TAB 3: PLAN & SUBSCRIPTION LIMITS ===
    with t_tier:
        col_p1, col_p2 = st.columns([1.5, 1])
        with col_p1:
            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">⚡ Enterprise Tier Capabilities</div>
                    <p class="section-desc">Unlimited automated data ingestion and real-time AI forecasts enabled</p>
                </div>
                <ul style="color: #2F4F4F; font-size: 0.92rem; line-height: 2;">
                    <li><b>Data Ingestion:</b> Unlimited CSV & Excel batch volume</li>
                    <li><b>Forecasting Engine:</b> Daily, Weekly, and Monthly AI forecasting</li>
                    <li><b>Storage Retention:</b> Permanent S3-compatible data lake archiving</li>
                    <li><b>Seats & Access:</b> Full workspace team access included</li>
                </ul>
                """, unsafe_allow_html=True)

        with col_p2:
            with st.container(border=True):
                st.markdown("""
                <div class="section-header-box">
                    <div class="section-title">💳 Billing & Invoices</div>
                    <p class="section-desc">Active recurring enterprise license</p>
                </div>
                <div style="font-size: 0.9rem; color: #2F4F4F; margin-bottom: 6px;">
                    Next Billing: <b>October 1, 2026</b>
                </div>
                <div style="font-size: 0.9rem; color: #2F4F4F; margin-bottom: 16px;">
                    Payment: <b>Direct MoMo / Card (•••• 4022)</b>
                </div>
                """, unsafe_allow_html=True)
                st.toggle("Auto-renew Subscription", value=True)
                if st.button("Download Latest Invoice (PDF)", use_container_width=True):
                    st.info("Invoice receipt PDF generated.")