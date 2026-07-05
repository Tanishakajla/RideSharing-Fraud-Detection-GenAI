import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests

API_URL = "http://127.0.0.1:8000"

FEATURE_ORDER = [
    'fare', 'seconds_since_signup', 'user_trip_count',
    'user_trips_last_1h', 'num_users_on_device',
    'device_degree', 'card_degree'
]

def call_investigate_api(features_dict):
    """Calls the FastAPI /investigate endpoint and returns the parsed JSON."""
    response = requests.post(f"{API_URL}/investigate", json=features_dict)
    response.raise_for_status()
    return response.json()

# --- Load Model and Data ---
@st.cache_data
def load_model():
    model = joblib.load('fraud_model.joblib')
    return model

model = load_model()
df = pd.read_csv('rideshare_fraud_data.csv')

# --- Dashboard Title ---
st.title("RideSharing - Fraud Detection Dashboard")

# --- Sidebar for User Input ---
st.sidebar.header("Input Features for Prediction")

fare = st.sidebar.slider("Fare Amount ($)", 5.0, 200.0, 50.0)
user_trip_count = st.sidebar.number_input("User's Previous Trip Count", min_value=0, max_value=500, value=10)
seconds_since_signup = st.sidebar.slider("Seconds Since User Signup", 1000, 15000000, 500000)
user_trips_last_1h = st.sidebar.number_input("User trips in last 1 hour", min_value=0, max_value=500, value=0)
num_users_on_device = st.sidebar.number_input("Number of users on device", min_value=0, max_value=100, value=1)
card_degree = st.sidebar.slider("Payment Card's Network Degree", 1, 50, 5)
device_degree = st.sidebar.slider("Device's Network Degree", 1, 50, 5)

# --- Session State Init ---
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "investigation_report" not in st.session_state:
    st.session_state.investigation_report = None

# Build the features dict once, reused by both buttons below
features_dict = {
    "fare": fare,
    "seconds_since_signup": seconds_since_signup,
    "user_trip_count": user_trip_count,
    "user_trips_last_1h": user_trips_last_1h,
    "num_users_on_device": num_users_on_device,
    "device_degree": device_degree,
    "card_degree": card_degree
}

# --- Button 1: Fast local prediction (no LLM) ---
if st.sidebar.button("Predict Fraud Risk"):
    # Pull values out of the dict IN A FIXED ORDER before turning into an array -
    # np.array() has no concept of feature names, only position, so order must match training order
    ordered_values = [features_dict[f] for f in FEATURE_ORDER]
    prediction_features = np.array(ordered_values).reshape(1, -1)

    probability = model.predict_proba(prediction_features)[0][1]

    st.session_state.prediction_result = probability
    st.session_state.last_features = features_dict

# --- Button 2: Full LLM investigation (slower) ---
if st.sidebar.button("🔍 Run Full Investigation (SHAP + LLM Report)"):
    with st.spinner("Running SHAP analysis and generating investigation report... (this takes a few seconds, the AI is thinking)"):
        try:
            result = call_investigate_api(features_dict)
            st.session_state.investigation_report = result
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Is `uvicorn Fraud:app --reload` running?")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# --- Display: Fast Prediction Result ---
if st.session_state.prediction_result is not None:
    st.subheader("Prediction Result")
    probability = st.session_state.prediction_result
    st.write(f"Probability (raw): {probability:.6f}")
    if probability > 0.5:
        st.error(f"High Fraud Risk Detected! (Probability: {probability:.2f})")
    else:
        st.success(f"Low Fraud Risk Detected. (Probability: {probability:.2f})")

    if "last_features" in st.session_state:
        st.write("Features sent to model:", st.session_state.last_features)

# --- Display: Full Investigation Report ---
if st.session_state.investigation_report is not None:
    report_data = st.session_state.investigation_report
    report = report_data["investigation_report"]

    st.subheader("🕵️ AI Investigation Report")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Fraud Probability", f"{report_data['fraud_probability']:.2%}")
    with col2:
        risk_level = report["risk_level"]
        color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk_level, "⚪")
        st.metric("Risk Level", f"{color} {risk_level.upper()}")

    st.markdown("**Summary:**")
    st.write(report["summary"])

    st.markdown("**Matched Fraud Patterns:**")
    for pattern in report["matched_fraud_patterns"]:
        st.markdown(f"- {pattern.replace('_', ' ').title()}")

    st.markdown("**Recommended Action:**")
    st.info(report["recommended_action"])

    st.markdown(f"*Confidence: {report['confidence_note']}*")

    with st.expander("🔬 View SHAP Feature Contributions (technical detail)"):
        contributions_df = pd.DataFrame(report_data["feature_contributions"])
        st.dataframe(contributions_df, use_container_width=True)

    with st.expander("📚 Retrieved Policy Sources"):
        st.write(f"Query used for retrieval: *{report['query_used']}*")
        for source in report["sources"]:
            st.markdown(f"- `{source}`")

# --- Display Raw Data ---
st.subheader("Raw Data Sample")
st.dataframe(df.head())