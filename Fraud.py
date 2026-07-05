from fastapi import FastAPI
import joblib
import pandas as pd
import shap
from pydantic import BaseModel
from generate_report import generate_investigation_report
from typing import Optional, List, Dict, Tuple, Any
from shap.explainers import TreeExplainer

app = FastAPI(
    title="RideSharing - Fraud Detection API",
    description="A real-time API to predict and explain ride-sharing transaction fraud risk."
)

class TripFeatures(BaseModel):
    fare: float
    seconds_since_signup: int
    user_trip_count: int
    user_trips_last_1h: int
    num_users_on_device: int
    device_degree: int
    card_degree: int

FEATURE_ORDER = [
    'fare', 'seconds_since_signup', 'user_trip_count',
    'user_trips_last_1h', 'num_users_on_device',
    'device_degree', 'card_degree'
]

model: Any = None
explainer: Any = None

def get_model() -> Tuple[Any, Any]:
    global model, explainer

    if model is None:
        model = joblib.load("fraud_model.joblib")
        explainer = shap.TreeExplainer(model)
    return model,explainer

def compute_shap_explanation(trip: TripFeatures) -> dict:
    df = trip_to_df(trip)
    probability = model.predict_proba(df)[0][1]

    shap_values = explainer(df)
    values = shap_values.values[0]
    if values.ndim == 2:
        values = values[:, 1]

    contributions = [
        {
            "feature": feat,
            "input_value": float(df.iloc[0][feat]),
            "shap_value": round(float(val), 4),
            "direction": "increases risk" if val > 0 else "decreases risk"
        }
        for feat, val in zip(FEATURE_ORDER, values)
    ]
    contributions.sort(key=lambda c: abs(c["shap_value"]), reverse=True)

    return {
        "fraud_probability": round(float(probability), 4),
        "feature_contributions": contributions
    }

    return model, explainer


def trip_to_df(trip: TripFeatures) -> pd.DataFrame:
    return pd.DataFrame([{
        'fare': trip.fare,
        'seconds_since_signup': trip.seconds_since_signup,
        'user_trip_count': trip.user_trip_count,
        'user_trips_last_1h': trip.user_trips_last_1h,
        'num_users_on_device': trip.num_users_on_device,
        'device_degree': trip.device_degree,
        'card_degree': trip.card_degree
    }])[FEATURE_ORDER]


@app.post("/predict")
def predict_fraud(trip: TripFeatures):
    model, explainer = get_model()
    df = trip_to_df(trip)
    probability = model.predict_proba(df)[0][1]
    return {"fraud_probability": round(float(probability), 4)}


@app.post("/explain")
def explain_fraud(trip: TripFeatures):
    return compute_shap_explanation(trip)

@app.post("/investigate")
def investigate_fraud(trip: TripFeatures):
    model, explainer = get_model()
    explain_result = compute_shap_explanation(trip)
    trip_dict = trip.model_dump()

    report = generate_investigation_report(explain_result, trip_dict)

    return {
        "fraud_probability": explain_result["fraud_probability"],
        "feature_contributions": explain_result["feature_contributions"],
        "investigation_report": report
    }