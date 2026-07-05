from retrieve import retrieve
from typing import Any,Optional
def build_query_from_shap(explain_result: dict, top_n: int = 3) -> str:
    """
    Convert the top-N SHAP feature contributions into a natural language
    description suitable for embedding search. Only features increasing
    risk are used to build the query - features pulling risk down aren't
    useful for finding "what fraud pattern is this."
    """
    contributions = explain_result["feature_contributions"]
    risky_features = [c for c in contributions if c["shap_value"] > 0]
    top_features = risky_features[:top_n]

    if not top_features:
        return "low risk transaction, no strong fraud signals"

    descriptions = []
    for feat in top_features:
        descriptions.append(f"{feat['feature']} = {feat['input_value']} (elevated risk contributor)")

    query = "Suspicious ride-sharing transaction with: " + ", ".join(descriptions)
    return query


def get_investigation_context(explain_result: dict, top_k_per_query: int = 2) -> dict[str, Any]:
    """
    Full pipeline: SHAP explanation -> query -> retrieved policy chunks.
    Returns deduplicated retrieved chunks, ranked by relevance score.
    """
    query = build_query_from_shap(explain_result)
    results = retrieve(query, top_k=top_k_per_query * 2)  # over-fetch, then dedupe

    # Dedupe by source_file - we don't want 3 chunks all from
    # velocity_fraud.md crowding out card_testing_fraud.md
    seen_files = set()
    deduped = []
    for r in results:
        if r["source_file"] not in seen_files:
            deduped.append(r)
            seen_files.add(r["source_file"])
        if len(deduped) >= top_k_per_query + 1:
            break

    return {"query_used": query,
    "retrieved_context": deduped
    }


if __name__ == "__main__":
    # Manual test with a fake SHAP-style output, mimicking /explain response
    fake_explain_output = {
        "fraud_probability": 0.87,
        "feature_contributions": [
            {"feature": "user_trips_last_1h", "input_value": 6, "shap_value": 0.42, "direction": "increases risk"},
            {"feature": "device_degree", "input_value": 7, "shap_value": 0.31, "direction": "increases risk"},
            {"feature": "seconds_since_signup", "input_value": 90, "shap_value": 0.18, "direction": "increases risk"},
            {"feature": "fare", "input_value": 5.0, "shap_value": -0.02, "direction": "decreases risk"},
        ]
    }

    result = get_investigation_context(fake_explain_output)
    print("Query used:", result["query_used"])
    print()
    for chunk in result["retrieved_context"]:
        print(f"[{chunk['score']}] {chunk['source_file']} / {chunk['section']}")
        print(chunk["text"][:150], "...\n")