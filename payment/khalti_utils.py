import requests
from django.conf import settings

def initiate_khalti_payment(amount, purchase_order_id, purchase_order_name, return_url, website_url, customer_info=None):
    """
    Initiates a payment request to Khalti.
    Amount should be in Paisa.
    """
    url = getattr(settings, 'KHALTI_SANDBOX_API_URL', "https://dev.khalti.com/api/v2/epayment/initiate/")
    headers = {
        'Authorization': f'Key {settings.KHALTI_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "return_url": return_url,
        "website_url": website_url,
        "amount": int(amount), # in paisa
        "purchase_order_id": str(purchase_order_id),
        "purchase_order_name": purchase_order_name,
    }
    if customer_info:
        payload["customer_info"] = customer_info

    response = requests.post(url, headers=headers, json=payload)
    return response.json()

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
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
