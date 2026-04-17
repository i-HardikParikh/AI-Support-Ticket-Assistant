"""
Simple Streamlit UI for the AI Support Ticket Assistant.

Run:
    streamlit run src/streamlit_app.py
"""

import json

import httpx
import streamlit as st


st.set_page_config(page_title="AI Support Ticket Assistant", page_icon="🎫", layout="centered")

st.title("🎫 AI Support Ticket Assistant")
st.caption("Analyze support tickets using your FastAPI backend.")

default_api_url = "http://127.0.0.1:8000"
api_base_url = st.sidebar.text_input("API Base URL", value=default_api_url).strip().rstrip("/")
st.sidebar.markdown("Start backend first: `uvicorn src.main:app --reload`")


def check_health(base_url: str) -> tuple[bool, str]:
    """Check FastAPI health endpoint."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base_url}/health")
            response.raise_for_status()
        return True, "Backend is healthy."
    except Exception as exc:
        return False, f"Health check failed: {exc}"


with st.sidebar:
    if st.button("Check Backend Health"):
        ok, message = check_health(api_base_url)
        if ok:
            st.success(message)
        else:
            st.error(message)


sample_ticket = (
    "I was charged twice this month, and this has not been resolved for 3 days. "
    "Please process a refund."
)

ticket_text = st.text_area(
    "Paste customer ticket",
    value=sample_ticket,
    height=180,
    max_chars=5000,
    help="Enter the raw support ticket text to analyze.",
)

analyze_clicked = st.button("Analyze Ticket", type="primary", use_container_width=True)

if analyze_clicked:
    cleaned = ticket_text.strip()
    if not cleaned:
        st.warning("Please enter a ticket before analyzing.")
    else:
        with st.spinner("Analyzing ticket..."):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{api_base_url}/analyze-ticket",
                        json={"ticket": cleaned},
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code >= 400:
                    detail = response.text
                    try:
                        payload = response.json()
                        detail = payload.get("detail", detail)
                    except json.JSONDecodeError:
                        pass
                    st.error(f"API error ({response.status_code}): {detail}")
                else:
                    data = response.json()
                    st.success("Analysis complete.")

                    col1, col2 = st.columns(2)
                    col1.metric("Category", str(data.get("category", "n/a")).title())
                    col2.metric("Escalation", "Yes" if data.get("escalation") else "No")

                    confidence = float(data.get("confidence", 0.0))
                    st.write("Confidence")
                    st.progress(min(max(confidence, 0.0), 1.0))
                    st.caption(f"{confidence:.2f}")

                    st.subheader("Draft Reply")
                    st.write(data.get("draft_reply", ""))

                    st.subheader("Reason")
                    st.write(data.get("reason", ""))

                    with st.expander("Raw JSON response"):
                        st.json(data)

            except Exception as exc:
                st.error(f"Request failed: {exc}")
