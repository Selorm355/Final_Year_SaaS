import os
import requests
import json
import base64
import uuid
from datetime import datetime
import user_connection as uc

# =========================================================
# --- 1. CONFIGURATION & MASTER PRICING SWITCH ---
# =========================================================

# 🚨 THE MASTER SWITCH: Set to False when deploying for commercial production!
IS_DEMO_MODE = True

# Load Hubtel credentials from environment variables (with empty fallbacks for safety)
HUBTEL_CLIENT_ID = os.getenv("HUBTEL_CLIENT_ID", "")
HUBTEL_CLIENT_SECRET = os.getenv("HUBTEL_CLIENT_SECRET", "")
HUBTEL_MERCHANT_ACCOUNT = os.getenv("HUBTEL_MERCHANT_ACCOUNT_NUMBER", "")

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

# Helper: Check if live Hubtel keys are configured
def is_live_hubtel_configured():
    return bool(HUBTEL_CLIENT_ID and HUBTEL_CLIENT_SECRET and HUBTEL_MERCHANT_ACCOUNT)


# =========================================================
# --- 2. INITIATE HOSTED CHECKOUT LINK ---
# =========================================================

def create_checkout_link(company_id, company_name, email, plan_key="MONTHLY", return_url="http://localhost:8501"):
    """
    1. Generates a unique client transaction reference.
    2. Writes a PENDING transaction receipt to PostgreSQL.
    3. Calls Hubtel to generate a Mobile Money checkout URL.
    """
    plan = PRICING_PLANS.get(plan_key.upper(), PRICING_PLANS["MONTHLY"])
    amount = plan["price_ghs"]
    
    # Generate unique reference (e.g., OMNI-1-8F3A2B)
    unique_suffix = uuid.uuid4().hex[:6].upper()
    client_reference = f"OMNI-{company_id}-{unique_suffix}"
    
    # Step 1: Record the pending receipt in our local database
    db_success = uc.record_pending_transaction(
        company_id=company_id,
        client_reference=client_reference,
        amount=amount,
        plan_type=plan_key
    )
    
    if not db_success:
        return False, "Database error: Could not record pending transaction.", None

    # Step 2: Check if we are running in Mock Mode (No keys configured)
    if not is_live_hubtel_configured():
        mock_url = f"{return_url}?mock_payment=true&ref={client_reference}&amount={amount}"
        print(f"⚠️ [MOCK MODE] Hubtel keys missing. Generating simulated checkout link for {client_reference}")
        return True, mock_url, client_reference

    # Step 3: Call Live Hubtel API (PayProxy Initiate Endpoint)
    endpoint = "https://payproxyapi.hubtel.com/items/initiate"
    
    # Base64 encode ClientID:ClientSecret for Basic Auth
    auth_string = f"{HUBTEL_CLIENT_ID}:{HUBTEL_CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "totalAmount": amount,
        "description": plan["description"],
        "callbackUrl": f"{return_url}/api/webhook/hubtel", # Background webhook (Optional for local testing)
        "returnUrl": return_url,                           # Where user lands after MoMo prompt
        "merchantAccountNumber": HUBTEL_MERCHANT_ACCOUNT,
        "cancellationUrl": return_url,
        "clientReference": client_reference
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            checkout_url = data.get("data", {}).get("checkoutUrl")
            if checkout_url:
                return True, checkout_url, client_reference
                
        # If Hubtel rejects the request, return the error
        error_msg = f"Hubtel API Error ({response.status_code}): {response.text}"
        return False, error_msg, client_reference
        
    except requests.exceptions.RequestException as e:
        return False, f"Network error connecting to Hubtel: {str(e)}", client_reference


# =========================================================
# --- 3. ACTIVE STATUS POLLING (VERIFY PAYMENT) ---
# =========================================================

def verify_payment_status(company_id, client_reference):
    """
    Powered by the '🔄 Verify Payment Status' button in Streamlit.
    Checks if the transaction succeeded. If so, activates the subscription in PostgreSQL.
    """
    # 1. Look up the pending transaction in PostgreSQL
    tx = uc.get_pending_transaction(client_reference)
    if not tx:
        return False, "Transaction reference not found in database."
        
    if tx['payment_status'] == 'SUCCESS':
        return True, "This subscription is already active!"
        
    plan_key = tx['plan_type']
    plan = PRICING_PLANS.get(plan_key.upper(), PRICING_PLANS["MONTHLY"])
    
    # Step 2: Check if we are in Mock Mode (Simulate instant MoMo success!)
    if not is_live_hubtel_configured():
        print(f"⚠️ [MOCK MODE] Simulating successful payment verification for {client_reference}")
        success, msg = uc.activate_subscription_and_log_transaction(
            company_id=company_id,
            client_reference=client_reference,
            hubtel_tx_id=f"MOCK-HUBTEL-{uuid.uuid4().hex[:8].upper()}",
            payment_method="MOCK_MTN_MOMO",
            plan_type=plan_key,
            duration_days=plan["duration_days"]
        )
        return success, f"[Demo Mode] {msg}"

    # Step 3: Call Live Hubtel Transaction Status API
    # Hubtel standard status check endpoint
    endpoint = f"https://api-stat.hubtel.com/v1/merchantaccount/merchants/{HUBTEL_MERCHANT_ACCOUNT}/transactions/status?clientReference={client_reference}"
    
    auth_string = f"{HUBTEL_CLIENT_ID}:{HUBTEL_CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Hubtel returns '0000' or '00' or status 'Success' for completed MoMo charges
            response_code = data.get("responseCode")
            status_text = data.get("data", {}).get("status", "").upper()
            
            if response_code in ["0000", "00"] or status_text in ["SUCCESS", "PAID"]:
                hubtel_tx_id = data.get("data", {}).get("transactionId", "UNKNOWN-HUBTEL-ID")
                payment_method = data.get("data", {}).get("paymentMethod", "MTN_MOMO")
                
                # Unlock database tier!
                success, msg = uc.activate_subscription_and_log_transaction(
                    company_id=company_id,
                    client_reference=client_reference,
                    hubtel_tx_id=hubtel_tx_id,
                    payment_method=payment_method,
                    plan_type=plan_key,
                    duration_days=plan["duration_days"]
                )
                return success, msg
            else:
                return False, f"Payment pending or not approved on phone yet. (Status: {status_text or 'Pending'})"
                
        return False, f"Could not verify with Hubtel server. Status code: {response.status_code}"
        
    except requests.exceptions.RequestException as e:
        return False, f"Network timeout while checking payment status: {str(e)}"