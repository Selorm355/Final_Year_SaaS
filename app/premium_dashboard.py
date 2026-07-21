import streamlit as st
import user_connection as uc
import payment_engine as pe

# =========================================================
# --- 1. THE PAYWALL UI (Shown when trial views hit 0) ---
# =========================================================

def render_paywall_card(company_id, company_name, email):
    """Renders an enterprise upgrade card when trial views are exhausted."""
    st.markdown("---") 
    
    # Modern styled box using Streamlit container
    with st.container(border=True):
        st.markdown(f"### 🔒 Workspace Locked: Free Trial Ended")
        st.write(
            f"**{company_name}**, your free workspace trial credits have been exhausted. "
            "Upgrade to an active subscription to unlock unlimited AI forecasting, automated ETL pipelines, "
            "and multi-tenant branch analytics across your industry."
        )
        
        st.markdown("#### Choose Your Growth Plan:")
        col1, col2 = st.columns(2)
        
        # --- PLAN 1: MONTHLY ---
        with col1:
            with st.container(border=True):
                st.markdown("### Pro Workspace")
                st.markdown(f"## **GHS {pe.PRICING_PLANS['MONTHLY']['price_ghs']:.2f}** `/ month`")
                st.write("✅ Unlimited Data Ingestion")
                st.write("✅ Automated Cleaning Pipelines")
                st.write("✅ Standard AI Forecasting")
                st.write("✅ Single-Branch Analytics")
                
                if st.button("🚀 Upgrade Monthly", key="btn_monthly", use_container_width=True):
                    with st.spinner("Generating secure Hubtel MoMo checkout link..."):
                        success, url_or_msg, ref = pe.create_checkout_link(
                            company_id, company_name, email, plan_key="MONTHLY"
                        )
                        if success:
                            st.session_state["pending_tx_ref"] = ref
                            st.session_state["checkout_url"] = url_or_msg
                            st.rerun()
                        else:
                            st.error(f"Gateway Error: {url_or_msg}")

        # --- PLAN 2: YEARLY ---
        with col2:
            with st.container(border=True):
                st.markdown("### Enterprise Workspace")
                st.markdown(f"## **GHS {pe.PRICING_PLANS['YEARLY']['price_ghs']:.2f}** `/ year`")
                st.write("✅ **Everything in Pro Workspace**")
                st.write("✅ **2 Months Free Discount**")
                st.write("✅ Multi-Branch Tenant Comparison")
                st.write("✅ Priority Webhook Processing")
                
                if st.button("👑 Upgrade Yearly (Best Value)", key="btn_yearly", type="primary", use_container_width=True):
                    with st.spinner("Generating secure Hubtel MoMo checkout link..."):
                        success, url_or_msg, ref = pe.create_checkout_link(
                            company_id, company_name, email, plan_key="YEARLY"
                        )
                        if success:
                            st.session_state["pending_tx_ref"] = ref
                            st.session_state["checkout_url"] = url_or_msg
                            st.rerun()
                        else:
                            st.error(f"Gateway Error: {url_or_msg}")

        # =========================================================
        # --- ACTIVE PAYMENT POLLING AREA (When link is generated) ---
        # =========================================================
        if "pending_tx_ref" in st.session_state and "checkout_url" in st.session_state:
            st.markdown("---")
            st.info(f"📱 **Action Required:** A payment request reference (`{st.session_state['pending_tx_ref']}`) has been initiated.")
            
            # Button 1: Send them to Hubtel to type MoMo number
            st.link_button(
                "👉 Step 1: Click Here to Authorize Payment on Hubtel", 
                st.session_state["checkout_url"], 
                type="primary", 
                use_container_width=True
            )
            
            st.write("*After approving the USSD prompt on your mobile phone, click the button below to unlock your workspace:*")
            
            # Button 2: Active polling button to check status
            if st.button("🔄 Step 2: Verify Payment Status", key="btn_verify", use_container_width=True):
                with st.spinner("Checking transaction status with cellular network..."):
                    verified, msg = pe.verify_payment_status(
                        company_id, 
                        st.session_state["pending_tx_ref"]
                    )
                    if verified:
                        st.success(f"🎉 {msg}")
                        # Clean up session state and reload page to drop paywall!
                        del st.session_state["pending_tx_ref"]
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
        route_to_industry_dashboard(company_id)  # 🚨 Passes company_id into your real chart function!
        return

    # --- STATE B: FREE TRIAL WITH VIEWS REMAINING (> 0) ---
    if views_left > 0:
        # Deduct 1 credit for this view
        new_views_left = uc.consume_trial_view(company_id)
        
        st.warning(
            f"💡 **Freemium Mode:** You have **{new_views_left} free dashboard view(s)** remaining "
            "across your workspace before hitting the paywall. Upgrade early to prevent workflow interruption!"
        )
        route_to_industry_dashboard(company_id)  # 🚨 Passes company_id into your real chart function!
        return

    # --- STATE C: FREE TRIAL EXHAUSTED (0 VIEWS LEFT) ---
    # Block the charts completely and show the paywall!
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

    # 2. Dynamically import and trigger your existing functions without altering your code!
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