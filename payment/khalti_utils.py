import requests
from django.conf import settings

def initiate_khalti_payment(amount, purchase_order_id, purchase_order_name, return_url, website_url, customer_info=None):
    """
    Initiates a payment request to Khalti.
    Amount should be in Paisa.
    """
    # Sanitize purchase_order_name: remove commas, dots and extra spaces which can break the API
    purchase_order_name = str(purchase_order_name).replace(',', '').replace('.', '').strip()
    
    url = getattr(settings, 'KHALTI_SANDBOX_API_URL', "https://dev.khalti.com/api/v2/epayment/initiate/")
    headers = {
        'Authorization': f'Key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "return_url": return_url,
        "website_url": website_url,
        "amount": int(float(amount)), # Ensure it's a flat integer in paisa
        "purchase_order_id": str(purchase_order_id),
        "purchase_order_name": purchase_order_name,
    }
    if customer_info:
        # Ensure customer_info only has valid keys
        valid_customer_info = {}
        for key in ['name', 'email', 'phone']:
            if key in customer_info and customer_info[key]:
                valid_customer_info[key] = str(customer_info[key])
        if valid_customer_info:
            payload["customer_info"] = valid_customer_info

    print(f"DEBUG: Khalti URL: {url}")
    print(f"DEBUG: Khalti Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        print(f"DEBUG: Khalti Status: {response.status_code}")
        print(f"DEBUG: Khalti Response: {response.text}")
        
        # Catch 400 errors specifically to return better details
        if response.status_code == 400:
            return response.json()
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error_key": "timeout", "detail": "Connection to Khalti payment gateway timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.json()
            except Exception:
                pass
        return {"error_key": "network_error", "detail": f"Network error when connecting to Khalti: {str(e)}"}

def verify_khalti_payment(pidx):
    """
    Verifies a payment status with Khalti.
    """
    url = getattr(settings, 'KHALTI_SANDBOX_LOOKUP_URL', "https://dev.khalti.com/api/v2/epayment/lookup/")
    headers = {
        'Authorization': f'Key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "pidx": pidx
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error_key": "timeout", "detail": "Connection to Khalti payment gateway timed out."}
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                return e.response.json()
            except Exception:
                pass
        return {"error_key": "network_error", "detail": f"Network error: {str(e)}"}
