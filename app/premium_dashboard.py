import streamlit as st

#this code has nothing to do with the medallion architecture, it is linked to the main.py it is where the premium dashboard is built.
# We will import the industry-specific files here
# (We will create dashboard_retail.py in the next step!)
import dashboard_retail 
import dashboard_healthcare
import dashboard_hospitality

def show_dashboard():
    st.title("📈 AI Forecasting & Analytics")

    # 1. THE BOUNCER
    if not st.session_state.get("logged_in"):
        st.warning("⚠️ Please log in to view your Premium Dashboard.")
        return

    company_name = st.session_state.get("company_name", "Your Company")
    industry = st.session_state.get("industry", "retail").lower()
    company_id = st.session_state.get("company_id")

    # 2. THE CASHIER (The Paywall Logic)
    # For your presentation, we are granting automatic Premium access.
    # Later, you will change this to fetch their status from the Postgres user table!
    subscription_status = "Premium" 

    if subscription_status != "Premium":
        st.error("🔒 Premium Feature Locked")
        st.write("Unlock AI Forecasting, deep business insights, and multi-year trend analysis.")
        st.button("Start 7-Day Free Trial / Paystack 💳")
        # In the future, you can put a blurred-out image of a chart here to tease them!
        return

    # 3. THE TRAFFIC COP (Routing to the correct charts)
    st.write(f"Welcome to your Premium {industry.capitalize()} Command Center, **{company_name}**.")
    st.divider()

    if industry == "retail":
        dashboard_retail.render_dashboard(company_id)
        
    elif industry == "healthcare":
         # st.info("🏥 Healthcare dashboard module is currently under construction.")
        dashboard_healthcare.render_dashboard(company_id)
        
    elif industry == "hospitality":
        # st.info("🏨 Hospitality dashboard module is currently under construction.")
        dashboard_hospitality.render_dashboard(company_id)
        
    else:
        st.error("Industry not recognized.")