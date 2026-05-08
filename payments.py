import stripe
import os
import json
import hashlib
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

PAID_SESSIONS_FILE = Path("paid_sessions.json")

def load_paid_sessions():
    if PAID_SESSIONS_FILE.exists():
        with open(PAID_SESSIONS_FILE) as f:
            return json.load(f)
    return {}

def save_paid_session(email: str):
    sessions = load_paid_sessions()
    key = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    sessions[key] = True
    with open(PAID_SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

def is_paid(email: str) -> bool:
    sessions = load_paid_sessions()
    key = hashlib.sha256(email.lower().strip().encode()).hexdigest()
    return sessions.get(key, False)

def create_checkout_session(email: str, success_url: str, cancel_url: str) -> str:
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "HOA Document Full Analysis",
                    "description": "Complete AI analysis: rental rules, red flags, reserve fund, key clauses, and verdict"
                },
                "unit_amount": 999,  # $9.99
            },
            "quantity": 1,
        }],
        mode="payment",
        customer_email=email,
        success_url=success_url + "?paid=true&email=" + email,
        cancel_url=cancel_url,
    )
    return session.url
