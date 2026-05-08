import streamlit as st
import os
from dotenv import load_dotenv
from analyzer import extract_text, analyze_hoa
from payments import is_paid, save_paid_session, create_checkout_session

load_dotenv()

st.set_page_config(
    page_title="HOA Analyzer — AI-Powered HOA Document Review",
    page_icon="🏠",
    layout="centered"
)

# ── Handle Stripe return ───────────────────────────────────────────────────
params = st.query_params
if params.get("paid") == "true" and params.get("email"):
    email = params.get("email")
    save_paid_session(email)
    st.query_params.clear()
    st.session_state["paid_email"] = email
    st.success(f"Payment confirmed for {email}. Upload your HOA document below.")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🏠 HOA Analyzer")
st.subheader("AI-powered HOA document review — know what you're buying into")
st.markdown(
    "Upload your HOA CC&Rs, bylaws, or disclosure documents. "
    "Get a plain-English summary of rental rules, pet policies, red flags, "
    "reserve fund status, and an overall risk verdict in under 60 seconds."
)

st.divider()

# ── Free preview vs paid ───────────────────────────────────────────────────
paid_email = st.session_state.get("paid_email", "")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("**Free Preview** — Summary + top 3 issues + verdict")
    st.markdown("**Full Report ($9.99)** — Everything: rental rules, reserve fund, pet policy, key clauses, red flags, insurance, maintenance breakdown")

with col2:
    st.metric("Price", "$9.99", "One-time")

st.divider()

# ── Upload ─────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload HOA Document (PDF)",
    type=["pdf"],
    help="CC&Rs, bylaws, rules and regulations, or any HOA disclosure document"
)

email_input = st.text_input(
    "Your email address",
    value=paid_email,
    placeholder="you@example.com",
    help="Required for payment and to retrieve your full report"
)

if uploaded_file and email_input:
    already_paid = is_paid(email_input)

    col_free, col_paid = st.columns(2)

    with col_free:
        if st.button("Get Free Preview", use_container_width=True):
            with st.spinner("Analyzing document..."):
                text = extract_text(uploaded_file)
                if len(text) < 200:
                    st.error("Could not extract text from this PDF. Please ensure it is not a scanned image.")
                else:
                    result = analyze_hoa(text, full=False)
                    st.session_state["preview_result"] = result
                    st.session_state["doc_text"] = text

    with col_paid:
        if already_paid:
            if st.button("Get Full Report (Paid)", type="primary", use_container_width=True):
                with st.spinner("Generating full report..."):
                    text = st.session_state.get("doc_text") or extract_text(uploaded_file)
                    result = analyze_hoa(text, full=True)
                    st.session_state["full_result"] = result
        else:
            base_url = os.environ.get("APP_URL", "http://localhost:8501")
            if st.button("Unlock Full Report — $9.99", type="primary", use_container_width=True):
                checkout_url = create_checkout_session(
                    email=email_input,
                    success_url=base_url,
                    cancel_url=base_url
                )
                st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                st.link_button("Click here to pay", checkout_url)

# ── Display free preview results ───────────────────────────────────────────
if "preview_result" in st.session_state:
    r = st.session_state["preview_result"]
    st.divider()
    st.markdown("## Free Preview")

    verdict_color = {"Low Risk": "green", "Medium Risk": "orange", "High Risk": "red"}
    verdict = r.get("verdict", "Unknown")
    color = verdict_color.get(verdict.split()[0] + " " + verdict.split()[1] if len(verdict.split()) > 1 else verdict, "gray")
    st.markdown(f"### Verdict: :{color}[{verdict}]")

    st.markdown("**Summary**")
    st.info(r.get("summary", ""))

    st.markdown("**Top 3 Things You Must Know**")
    for i, issue in enumerate(r.get("top_issues", []), 1):
        st.markdown(f"{i}. {issue}")

    if r.get("red_flags"):
        st.markdown("**Red Flags**")
        for flag in r.get("red_flags", []):
            st.error(f"⚠️ {flag}")

    st.divider()
    st.markdown("*Unlock the full report for rental restrictions, reserve fund status, pet policy, insurance breakdown, key rules, and more.*")

# ── Display full report ────────────────────────────────────────────────────
if "full_result" in st.session_state:
    r = st.session_state["full_result"]
    st.divider()
    st.markdown("## Full Report")

    verdict_color = {"Low": "green", "Medium": "orange", "High": "red"}
    verdict = r.get("verdict", "")
    color = verdict_color.get(verdict.split()[0], "gray")
    st.markdown(f"### Verdict: :{color}[{verdict}]")

    st.info(r.get("summary", ""))

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Monthly HOA Fee**")
        st.write(r.get("monthly_fees", "Not mentioned"))
        st.markdown("**Reserve Fund**")
        st.write(r.get("reserve_fund", "Not mentioned"))
        st.markdown("**Rental Restrictions**")
        st.write(r.get("rental_restrictions", "Not mentioned"))
        st.markdown("**Pet Policy**")
        st.write(r.get("pet_policy", "Not mentioned"))

    with col_b:
        st.markdown("**Special Assessments**")
        st.write(r.get("special_assessments", "None mentioned"))
        st.markdown("**Litigation**")
        st.write(r.get("litigation", "None mentioned"))
        st.markdown("**Insurance**")
        st.write(r.get("insurance", "Not mentioned"))
        st.markdown("**Maintenance**")
        st.write(r.get("maintenance_responsibility", "Not mentioned"))

    st.markdown("**Top Issues**")
    for i, issue in enumerate(r.get("top_issues", []), 1):
        st.markdown(f"{i}. {issue}")

    if r.get("red_flags"):
        st.markdown("**Red Flags**")
        for flag in r.get("red_flags", []):
            st.error(f"⚠️ {flag}")

    if r.get("prohibited_uses"):
        st.markdown("**Prohibited Uses**")
        for use in r.get("prohibited_uses", []):
            st.markdown(f"- {use}")

    if r.get("key_rules"):
        st.markdown("**Key Rules for New Owners**")
        for rule in r.get("key_rules", []):
            st.markdown(f"- {rule}")

# ── Footer ─────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "HOA Analyzer uses AI to summarize documents and is not legal advice. "
    "Always consult a real estate attorney before making purchase decisions."
)
