import streamlit as st
import os
import user_connection as uc 
import payment_engine as pe
import navigation

def inject_custom_css():
    """Reads the CSS file and injects it into Streamlit."""
    css_path = os.path.join(os.path.dirname(__file__), "global_style.css")
    try:
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# =========================================================
# --- 1. THE PAYWALL UI (Shown when trial views hit 0) ---
# =========================================================

def render_paywall_card(company_id, company_name, email):
    """Renders an enterprise upgrade card when trial views are exhausted."""
    st.markdown("---")
    
    with st.container(border=True):
        st.markdown(f"### 🔒 Workspace Locked: Free Trial Ended")
        
        # POLISHED: Business-friendly customer benefits (No technical jargon!)
        st.write(
            f"**{company_name}**, your free workspace trial credits have been exhausted. "
            "Upgrade to an active subscription to unlock unlimited AI revenue forecasting, automated "
            "daily data synchronization, and multi-location performance tracking across your entire business."
        )
        
        st.markdown("#### Choose Your Growth Plan:")
        col1, col2 = st.columns(2)
        
        # =========================================================
        # --- COLUMN 1: PRO WORKSPACE (MONTHLY) ---
        # =========================================================
        with col1:
            with st.container(border=True):
                st.markdown("### Pro Workspace")
                monthly_price = pe.PRICING_PLANS["MONTHLY"]["price_ghs"]
                st.markdown(f"## **GHS {monthly_price:.2f}** / month")
                st.markdown("✅ Unlimited Data Ingestion")
                st.markdown("✅ Automated Cleaning Pipelines")
                st.markdown("✅ Standard AI Forecasting")
                st.markdown("✅ Single-Branch Analytics")
                
                if st.button("🚀 Upgrade Monthly", key="btn_monthly", use_container_width=True):
                    with st.spinner("Generating Paystack checkout link..."):
                        success, checkout_url, ref = pe.create_checkout_link(
                            company_id=company_id,
                            company_name=company_name,
                            email=email,
                            plan_key="MONTHLY"
                        )
                        if success:
                            st.session_state["pending_tx_ref"] = ref
                            st.session_state["checkout_url"] = checkout_url
                            st.rerun()
                        else:
                            st.error(f"Failed to initiate payment: {checkout_url}")

        # =========================================================
        # --- COLUMN 2: ENTERPRISE WORKSPACE (YEARLY) ---
        # =========================================================
        with col2:
            with st.container(border=True):
                st.markdown("### Enterprise Workspace")
                yearly_price = pe.PRICING_PLANS["YEARLY"]["price_ghs"]
                st.markdown(f"## **GHS {yearly_price:.2f}** / year")
                st.markdown("✅ Everything in Pro Workspace")
                st.markdown("✅ 2 Months Free Discount")
                st.markdown("✅ Multi-Branch Tenant Comparison")
                st.markdown("✅ Priority Webhook Processing")
                
                if st.button("👑 Upgrade Yearly (Best Value)", key="btn_yearly", type="primary", use_container_width=True):
                    with st.spinner("Generating Paystack checkout link..."):
                        success, checkout_url, ref = pe.create_checkout_link(
                            company_id=company_id,
                            company_name=company_name,
                            email=email,
                            plan_key="YEARLY"
                        )
                        if success:
                            st.session_state["pending_tx_ref"] = ref
                            st.session_state["checkout_url"] = checkout_url
                            st.rerun()
                        else:
                            st.error(f"Failed to initiate payment: {checkout_url}")

        # =========================================================
        # --- ACTIVE PAYMENT POLLING AREA ---
        # =========================================================
        if "pending_tx_ref" in st.session_state and "checkout_url" in st.session_state:
            st.markdown("---")
            
            # POLISHED: Friendlier payment initiation notice
            st.info(
                f"📱 **Payment Initiated:** Your secure transaction reference is "
                f"**`{st.session_state['pending_tx_ref']}`**. Please complete the prompt on your mobile device."
            )
            
            st.link_button(
                "👉 Step 1: Click Here to Authorize Payment on Paystack", 
                st.session_state["checkout_url"], 
                type="primary", 
                use_container_width=True
            )
            
            st.write("*After approving the prompt on your mobile screen, click the button below to unlock your workspace:*")
            
            if st.button("🔄 Step 2: Verify Payment Status", key="btn_verify", use_container_width=True):
                with st.spinner("Checking transaction status with Paystack..."):
                    verified, msg = pe.verify_payment_status(
                        company_id, 
                        st.session_state["pending_tx_ref"]
                    )
                    if verified:
                        st.success(f"🎉 {msg}")
                        if "pending_tx_ref" in st.session_state:
                            del st.session_state["pending_tx_ref"]
                        if "checkout_url" in st.session_state:
                            del st.session_state["checkout_url"]
                        st.rerun()
                    else:
                        st.warning(f"⏳ {msg}")


# =========================================================
# --- 2. THE MASTER GATEKEEPER (Call this from main.py) ---
# =========================================================

def render_dashboard_gatekeeper():
    """
    Main entry point for the Premium Dashboard page.
    Checks database subscription tier and trial credits before rendering graphs.
    """
    
    navigation.render_back_button("Data Preview", "Data Preview")

    # Inject custom CSS layout immediately upon page load
    inject_custom_css()
    
    # 0. CATCH PAYSTACK REDIRECT: Check if Paystack sent the user back with a reference in the URL!
    query_params = st.query_params
    if "reference" in query_params:
        ref_from_url = query_params["reference"]
        
        # We need a company_id to verify. Let's extract safely from session or query
        has_user_dict = "user" in st.session_state and bool(st.session_state["user"])
        company_id = st.session_state["user"]["company_id"] if has_user_dict else st.session_state.get("company_id")
        
        if company_id:
            with st.spinner("Processing payment return from Paystack..."):
                verified, msg = pe.verify_payment_status(company_id, ref_from_url)
                if verified:
                    st.success(f"🎉 {msg}")
                    # Clear query params so it doesn't loop verification on refresh
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.warning(f"⏳ Payment verification status: {msg}")

    # 1. Ensure user is authenticated (checks both standard login and token login)
    is_logged_in = st.session_state.get("logged_in", False)
    has_user_dict = "user" in st.session_state and bool(st.session_state["user"])
    
    if not is_logged_in and not has_user_dict:
        st.warning("⚠️ Please log in from the sidebar to access the analytics workspace.")
        return

    # 2. Extract user details safely regardless of how auth.py saved them!
    if has_user_dict:
        company_id = st.session_state["user"]["company_id"]
        company_name = st.session_state["user"]["company_name"]
        email = st.session_state["user"].get("email", "admin@omnipulse.com")
    else:
        company_id = st.session_state.get("company_id")
        company_name = st.session_state.get("company_name")
        email = st.session_state.get("email", "admin@omnipulse.com")

    # If somehow ID is missing, stop gracefully
    if not company_id:
        st.error("🚨 Workspace ID missing from session. Please log out and log in again.")
        return

    # 3. Fetch live subscription & credit info from PostgreSQL
    sub_info = uc.get_subscription_info(company_id)
    if not sub_info:
        st.error("Could not retrieve workspace billing details from database.")
        return

    is_paid = sub_info["is_paid"]
    views_left = sub_info["views_left"]

    # --- STATE A: ACTIVE PAID SUBSCRIBER ---
    if is_paid:
        st.success(f"👑 **Active Subscription ({sub_info['tier']} Tier):** Unlimited workspace access enabled.")
        route_to_industry_dashboard(company_id)  
        return

    # --- STATE B: FREE TRIAL WITH VIEWS REMAINING (> 0) ---
    if views_left > 0:
        new_views_left = uc.consume_trial_view(company_id)
        
        st.warning(
            f"💡 **Freemium Mode:** You have **{new_views_left} free dashboard view(s)** remaining "
            "across your workspace before hitting the paywall. Upgrade early to prevent workflow interruption!"
        )
        route_to_industry_dashboard(company_id)  
        return

    # --- STATE C: FREE TRIAL EXHAUSTED (0 VIEWS LEFT) ---
    render_paywall_card(company_id, company_name, email)


# =========================================================
# --- 3. THE INDUSTRY TRAFFIC CONTROLLER (ROUTER) ---
# =========================================================

def route_to_industry_dashboard(company_id):
    """
    Reads the user's industry from session state and dynamically calls 
    your exact render_dashboard(company_id) function!
    """
    # 1. Grab the logged-in user's industry
    industry = st.session_state.get("industry")
    
    # Fallback check inside the user dictionary if top-level string is missing
    if not industry and "user" in st.session_state and isinstance(st.session_state["user"], dict):
        industry = st.session_state["user"].get("industry")
        
    # Default to Retail if none is specified
    if not industry:
        industry = "Retail"

    # 2. Dynamically import and trigger existing functions without altering code
    try:
        if industry.lower() == "healthcare":
            import dashboard_healthcare
            dashboard_healthcare.render_dashboard(company_id)
            
        elif industry.lower() == "hospitality":
            import dashboard_hospitality
            dashboard_hospitality.render_dashboard(company_id)
            
        else:
            # Defaults to Retail
            import dashboard_retail
            dashboard_retail.render_dashboard(company_id)
            
    except AttributeError as e:
        st.error(
            f"🚨 **Configuration Notice:** Connected to `{industry}` module, but could not find the `render_dashboard(company_id)` function inside it.\n\n"
            f"**System Error Details:** `{e}`"
        )
    except ImportError as e:
        st.error(
            f"🚨 **Module Missing:** Could not import `dashboard_{industry.lower()}.py`. Ensure the file is inside your `/app` directory.\n\n"
            f"**System Error Details:** `{e}`"
        )