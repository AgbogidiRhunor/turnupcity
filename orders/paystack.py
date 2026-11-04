import hmac
import hashlib
import json
import urllib.request
import urllib.error
from django.conf import settings


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = 'https://api.paystack.co'


def _make_request(method, endpoint, data=None):
    """Make a request to the Paystack API."""
    url = f"{PAYSTACK_BASE_URL}{endpoint}"
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            return json.loads(error_body)
        except Exception:
            return {'status': False, 'message': f'HTTP {e.code}: {error_body}'}
    except Exception as e:
        return {'status': False, 'message': str(e)}


def initialize_payment(email, amount_naira, reference, callback_url, metadata=None):
    """
    Initialize a Paystack payment.
    amount_naira: amount in Naira (will be converted to kobo).
    Returns the authorization_url to redirect the user to.
    """
    amount_kobo = int(float(amount_naira) * 100)
    data = {
        'email': email,
        'amount': amount_kobo,
        'reference': reference,
        'callback_url': callback_url,
        'currency': 'NGN',
    }
    if metadata:
        data['metadata'] = metadata

    response = _make_request('POST', '/transaction/initialize', data)
    return response


def verify_payment(reference):
    """
    Verify a Paystack payment by reference.
    Returns the full verification response.
    """
    response = _make_request('GET', f'/transaction/verify/{reference}')
    return response


def verify_webhook_signature(payload_body, signature):
    """
    Verify that a webhook request genuinely came from Paystack.
    payload_body: raw bytes of the request body.
    signature: value of X-Paystack-Signature header.
    """
    computed = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload_body,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, signature)

def get_banks():
    """Fetch list of Nigerian banks from Paystack."""
    response = _make_request('GET', '/bank?currency=NGN&perPage=100')
    return response


def resolve_account(account_number, bank_code):
    """
    Verify a bank account number with Paystack.
    Returns account_name if valid.
    """
    response = _make_request('GET', f'/bank/resolve?account_number={account_number}&bank_code={bank_code}')
    return response


def create_transfer_recipient(account_name, account_number, bank_code):
    """
    Create a Paystack transfer recipient.
    Must be done before initiating a transfer.
    Returns recipient_code used for transfers.
    """
    data = {
        'type': 'nuban',
        'name': account_name,
        'account_number': account_number,
        'bank_code': bank_code,
        'currency': 'NGN',
    }
    response = _make_request('POST', '/transferrecipient', data)
    return response


def initiate_transfer(amount_naira, recipient_code, reference, reason='TurnUpCity Withdrawal'):
    """
    Initiate a Paystack transfer to a recipient.
    amount_naira: amount in Naira (converted to kobo).
    recipient_code: from create_transfer_recipient().
    reference: unique reference for this transfer.
    """
    amount_kobo = int(float(amount_naira) * 100)
    data = {
        'source': 'balance',
        'amount': amount_kobo,
        'recipient': recipient_code,
        'reference': reference,
        'reason': reason,
    }
    response = _make_request('POST', '/transfer', data)
    return response


def verify_transfer(reference):
    """Verify a transfer status by reference."""
    response = _make_request('GET', f'/transfer/verify/{reference}')
    return response


def get_paystack_balance():
    """Get the current Paystack balance (in kobo)."""
    response = _make_request('GET', '/balance')
    return response
