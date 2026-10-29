import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class FedaPayError(Exception):
    pass


def _api_request(path, payload=None):
    api_key = getattr(settings, "FEDAPAY_API_KEY", "")
    if not api_key:
        raise FedaPayError("Le paiement en ligne n'est pas encore configuré.")

    environment = getattr(settings, "FEDAPAY_ENVIRONMENT", "sandbox")
    if environment not in {"sandbox", "live"}:
        raise FedaPayError("L'environnement FedaPay est invalide.")
    base = "https://sandbox-api.fedapay.com" if environment == "sandbox" else "https://api.fedapay.com"
    body = json.dumps(payload or {}).encode("utf-8")
    request = Request(
        f"{base}/v1/{path.lstrip('/')}",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FedaPayError("FedaPay n'a pas pu préparer le paiement. Réessayez plus tard.") from exc


def create_payment_link(*, email, description, amount_xof, callback_url):
    created = _api_request(
        "transactions",
        {
            "description": description,
            "amount": amount_xof,
            "currency": {"iso": "XOF"},
            "callback_url": callback_url,
            "customer": {"email": email},
        },
    )
    transaction = created.get("transaction", created.get("data", {}).get("transaction", {}))
    transaction_id = transaction.get("id")
    if not transaction_id:
        raise FedaPayError("FedaPay n'a pas retourné de numéro de transaction.")

    token_response = _api_request(f"transactions/{transaction_id}/token")
    token = token_response.get("token", token_response.get("data", {}).get("token", {}))
    payment_url = token.get("url") if isinstance(token, dict) else None
    if not payment_url:
        raise FedaPayError("FedaPay n'a pas retourné de lien de paiement.")
    return str(transaction_id), payment_url
