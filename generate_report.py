import json
import ollama
from investigation_context import get_investigation_context
from threshold_rules import evaluate_all_thresholds

MODEL_NAME = "llama3.2:3b"  # Ollama model name for the LLM used to generate investigation reports

SYSTEM_PROMPT = """You are a fraud investigation assistant for a ride-sharing platform.
You write concise, factual investigation summaries for human fraud analysts.

STRICT RULES:
1. Only use facts from the transaction data and the retrieved policy context given to you.
   Do not invent statistics, do not reference fraud patterns not present in the context.
2. Be specific: reference actual feature values and actual policy names given to you.
3. If the retrieved context doesn't clearly support a conclusion, say the evidence is
   inconclusive rather than guessing.
4. Respond with ONLY valid JSON matching this exact schema, no other text:

{
  "risk_level": "low" | "medium" | "high",
  "summary": "2-3 sentence plain-English explanation of why this was flagged",
  "matched_fraud_patterns": ["pattern name", ...],
  "recommended_action": "specific next step for the analyst",
  "confidence_note": "1 sentence on how strong the evidence is"
}"""


def build_user_prompt(explain_result: dict, context: dict, trip_dict: dict) -> str:
    contributions_text = "\n".join([
        f"- {c['feature']} = {c['input_value']} ({c['direction']}, SHAP contribution: {c['shap_value']})"
        for c in explain_result["feature_contributions"]
    ])
    verified_levels = evaluate_all_thresholds(trip_dict)
    verified_text = "\n".join([f"- {k}: {v}" for k, v in verified_levels.items()])
    policy_text = "\n\n".join([
        f"[Source: {c['source_file']} - {c['section']}]\n{c['text']}"
        for c in context["retrieved_context"]
    ])

    return f"""TRANSACTION DATA:
Fraud probability: {explain_result['fraud_probability']}

Feature contributions (sorted by impact):
{contributions_text}

RETRIEVED POLICY CONTEXT:
{policy_text}

PRE-VERIFIED THRESHOLD LEVELS (already calculated correctly - use these exact
levels in your summary, do not recalculate or contradict them):
{verified_text}

Write the investigation report as JSON per the schema."""


def generate_investigation_report(explain_result: dict, trip_dict: dict) -> dict:
    context = get_investigation_context(explain_result)
    user_prompt = build_user_prompt(explain_result, context, trip_dict)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        format="json"   # Ollama will constrain output to valid JSON
    )

    raw_content = response["message"]["content"]

    try:
        report = json.loads(raw_content)
    except json.JSONDecodeError:
        report = {
            "risk_level": "unknown",
            "summary": "Report generation failed to produce valid JSON.",
            "matched_fraud_patterns": [],
            "recommended_action": "Manual review required - LLM output error.",
            "confidence_note": "N/A",
            "raw_output": raw_content
        }

    report["query_used"] = context["query_used"]
    report["sources"] = [c["source_file"] for c in context["retrieved_context"]]
    return report


if __name__ == "__main__":
    fake_trip = {
        "fare": 5.0,
        "seconds_since_signup": 90,
        "user_trip_count": 1,
        "user_trips_last_1h": 6,
        "num_users_on_device": 4,
        "device_degree": 7,
        "card_degree": 3
    }
    fake_explain_output = {
        "fraud_probability": 0.87,
        "feature_contributions": [
            {"feature": "user_trips_last_1h", "input_value": 6, "shap_value": 0.42, "direction": "increases risk"},
            {"feature": "device_degree", "input_value": 7, "shap_value": 0.31, "direction": "increases risk"},
            {"feature": "seconds_since_signup", "input_value": 90, "shap_value": 0.18, "direction": "increases risk"},
            {"feature": "fare", "input_value": 5.0, "shap_value": -0.02, "direction": "decreases risk"},
        ]
    }

    report = generate_investigation_report(fake_explain_output, fake_trip)
    print(json.dumps(report, indent=2))