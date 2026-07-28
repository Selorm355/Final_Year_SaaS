import os
import requests
import json
import uuid
from datetime import datetime
import user_connection as uc

# =========================================================
# --- 1. CONFIGURATION & MASTER PRICING SWITCH ---
# =========================================================

# 🚨 THE MASTER SWITCH: Set to False when deploying for commercial production!
IS_DEMO_MODE = True

# Load Paystack Secret Key from environment variables
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "") 

# Centralized Pricing Engine
PRICING_PLANS = {
    "MONTHLY": {
        "name": "Pro Workspace (Monthly)",
        "price_ghs": 1.00 if IS_DEMO_MODE else 350.00,
        "duration_days": 30,
        "description": "OmniPulse Pro (Demo 1 GHS)" if IS_DEMO_MODE else "OmniPulse Pro Monthly Workspace"
    },
    "YEARLY": {
        "name": "Enterprise Workspace (Yearly)",
        "price_ghs": 10.00 if IS_DEMO_MODE else 3500.00,
        "duration_days": 365,
        "description": "OmniPulse Enterprise (Demo 10 GHS)" if IS_DEMO_MODE else "OmniPulse Enterprise Yearly Workspace"
    }
}

# Helper: Check if live/test Paystack Secret Key is configured
def is_live_paystack_configured():
    return bool(PAYSTACK_SECRET_KEY and PAYSTACK_SECRET_KEY.startswith("sk_"))


# =========================================================
# --- 2. INITIATE HOSTED CHECKOUT LINK ---
# =========================================================

def create_checkout_link(company_id, company_name, email, plan_key="MONTHLY", return_url="http://localhost:8501"):
    """
    1. Generates a unique client transaction reference.
    2. Writes a PENDING transaction receipt to PostgreSQL.
    3. Calls Paystack API to generate a hosted checkout URL.
    """
    plan = PRICING_PLANS.get(plan_key.upper(), PRICING_PLANS["MONTHLY"])
    amount_ghs = plan["price_ghs"]
    
    # Generate unique reference (e.g., OMNI-1-8F3A2B)
    unique_suffix = uuid.uuid4().hex[:6].upper()
    client_reference = f"OMNI-{company_id}-{unique_suffix}"
    
    # Step 1: Record the pending receipt in local PostgreSQL database
    db_success = uc.record_pending_transaction(
        company_id=company_id,
        client_reference=client_reference,
        amount=amount_ghs,
        plan_type=plan_key
    )
    
    if not db_success:
        return False, "Database error: Could not record pending transaction.", None

    # Step 2: Check if running in Mock Mode (No Paystack key configured)
    if not is_live_paystack_configured():
        mock_url = f"{return_url}?mock_payment=true&ref={client_reference}&amount={amount_ghs}"
        print(f"⚠️ [MOCK MODE] Paystack key missing. Generating simulated checkout link for {client_reference}")
        return True, mock_url, client_reference

    # Step 3: Call Paystack Initialize Endpoint
    endpoint = "https://api.paystack.co/transaction/initialize"
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    # Paystack requires amounts in currency subunits (Pesewas for GHS). 1 GHS = 100 Pesewas
    amount_in_pesewas = int(amount_ghs * 100)
    
    payload = {
        "email": email or "admin@omnipulse.com",
        "amount": amount_in_pesewas,
        "currency": "GHS",
        "reference": client_reference,
        "callback_url": return_url,
        "metadata": {
            "company_id": company_id,
            "company_name": company_name,
            "plan_key": plan_key,
            "custom_fields": [
                {
                    "display_name": "Workspace ID",
                    "variable_name": "company_id",
                    "value": str(company_id)
                }
            ]
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                checkout_url = data.get("data", {}).get("authorization_url")
                if checkout_url:
                    return True, checkout_url, client_reference
                
        # Handle API rejection
        error_msg = f"Paystack API Error ({response.status_code}): {response.text}"
        return False, error_msg, client_reference
        
    except requests.exceptions.RequestException as e:
        return False, f"Network error connecting to Paystack: {str(e)}", client_reference


# =========================================================
# --- 3. ACTIVE STATUS POLLING (VERIFY PAYMENT) ---
# =========================================================

def verify_payment_status(company_id, client_reference):
    """
    Powered by the '🔄 Verify Payment Status' button in Streamlit.
    Queries Paystack to confirm charge success. If verified, activates subscription in PostgreSQL.
    """
    # Step 1: Look up the pending transaction in local PostgreSQL
    tx = uc.get_pending_transaction(client_reference)
    if not tx:
        return False, "Transaction reference not found in database."
        
    if tx['payment_status'] == 'SUCCESS':
        return True, "This subscription is already active!"
        
    plan_key = tx['plan_type']
    plan = PRICING_PLANS.get(plan_key.upper(), PRICING_PLANS["MONTHLY"])
    
    # Step 2: Check if running in Mock Mode (Simulate instant success)
    if not is_live_paystack_configured():
        print(f"⚠️ [MOCK MODE] Simulating successful payment verification for {client_reference}")
        success, msg = uc.activate_subscription_and_log_transaction(
            company_id=company_id,
            client_reference=client_reference,
            hubtel_tx_id=f"MOCK-PAYSTACK-{uuid.uuid4().hex[:8].upper()}",
            payment_method="MOCK_MTN_MOMO",
            plan_type=plan_key,
            duration_days=plan["duration_days"]
        )
        return success, f"[Demo Mode] {msg}"

    # Step 3: Call Paystack Verify Endpoint
    endpoint = f"https://api.paystack.co/transaction/verify/{client_reference}"
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") and data.get("data", {}).get("status") == "success":
                tx_data = data.get("data", {})
                paystack_tx_id = str(tx_data.get("id", "UNKNOWN-PAYSTACK-ID"))
                channel = tx_data.get("channel", "mobile_money").upper()
                
                # Unlock database tier!
                success, msg = uc.activate_subscription_and_log_transaction(
                    company_id=company_id,
                    client_reference=client_reference,
                    hubtel_tx_id=paystack_tx_id,  # Column maps to gateway reference
                    payment_method=f"PAYSTACK_{channel}",
                    plan_type=plan_key,
                    duration_days=plan["duration_days"]
                )
                return success, msg
            else:
                paystack_status = data.get("data", {}).get("status", "pending")
                gateway_response = data.get("data", {}).get("gateway_response", "Payment not completed yet.")
                return False, f"Status: {paystack_status.capitalize()} ({gateway_response})"
                
        return False, f"Could not verify with Paystack server. (HTTP {response.status_code})"
        
    except requests.exceptions.RequestException as e:
        return False, f"Network timeout while checking payment status: {str(e)}"