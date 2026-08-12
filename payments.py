import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def is_paid(email: str) -> bool:
    """Ask Stripe directly whether this email has a completed payment.
    Stripe is the source of truth - no local state to lose on restart.
    Uses list() + manual filtering since the Search API doesn't cover
    Checkout Sessions."""
    target = email.lower().strip()
    sessions = stripe.checkout.Session.list(status="complete", limit=100)
    for session in sessions.auto_paging_iter():
        if session.customer_details and session.customer_details.email:
            if session.customer_details.email.lower().strip() == target:
                return True
    return False


def verify_checkout_session(session_id: str):
    """Verify a completed checkout directly with Stripe using the session id
    Stripe redirected back with - never trust client-supplied email/paid flags.
    Returns the verified email on success, or None if payment isn't confirmed."""
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid" and session.customer_details:
        return session.customer_details.email
    return None


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
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
    )
    return session.url
