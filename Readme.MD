# RideSharing— AI Fraud Investigation Assistant

An AI-powered fraud detection system for ride-sharing transactions. Combines
a machine learning classifier with SHAP explainability, retrieval-augmented
generation (RAG), and a local LLM to turn a raw fraud probability score into
a structured, human-readable investigation report for fraud analysts.

> Built on top of an open-source rideshare fraud detection baseline
> ([original repo](https://github.com/gouri-rabgotra21/RideSentry-Fraud-Detection) —
> LightGBM model + basic prediction API), significantly extended with SHAP-based
> explainability, a RAG-powered fraud policy knowledge base (FAISS), and an
> LLM-generated investigation reporting layer (Ollama / Llama 3.2).

---

## The Problem

A raw fraud probability score like `0.87` tells a fraud analyst *that*
something looks suspicious, but not *why*, and not *what to do about it*.
At scale, analysts can't manually dig through model internals for every
flagged transaction. This project closes that gap.

## What It Does

Given a ride transaction's features, the system:

1. Predicts a fraud probability using a trained LightGBM classifier
2. Explains *why*, using SHAP (SHapley Additive exPlanations) to rank which
   features drove the score up or down
3. Retrieves relevant fraud policy documentation (velocity fraud, device
   sharing, card testing, new-account fraud) using semantic search over a
   FAISS vector index
4. Cross-checks the transaction against hard-coded, verified policy
   thresholds in Python — so numeric conclusions are always correct, never
   left to LLM guesswork
5. Generates a structured, analyst-ready investigation report using a local
   LLM (Llama 3.2 via Ollama), grounded strictly in the retrieved policy
   text and verified thresholds — not the model's general "knowledge" about
   fraud

## Architecture

```
Trip Features
     │
     ▼
LightGBM Model ──► Fraud Probability
     │
     ▼
SHAP Explainer ──► Ranked Feature Contributions
     │
     ▼
Query Builder ──► Natural language description of risk signals
     │
     ▼
FAISS Retrieval ──► Relevant fraud policy chunks (from knowledge_base/)
     │
     ▼
Threshold Rules ──► Verified suspicion levels (Python, not LLM)
     │
     ▼
Ollama (Llama 3.2) ──► Structured JSON investigation report
     │
     ▼
FastAPI /investigate ──► Streamlit Dashboard
```

## Tech Stack

- **ML**: LightGBM, Scikit-learn, SHAP
- **RAG**: sentence-transformers (`all-MiniLM-L6-v2`), FAISS
- **LLM**: Ollama (Llama 3.2, fully local — no external API calls)
- **Backend**: FastAPI
- **Frontend**: Streamlit

## Key Design Decisions

- **Local LLM, not an external API** — keeps transaction data on-machine,
  no per-request cost, consistent with a privacy-conscious fraud system.
- **Threshold logic lives in Python, not in the prompt** — small LLMs are
  unreliable at precise numeric comparisons. All threshold decisions
  (e.g., "is this velocity moderate or high risk?") are computed
  deterministically in code and passed to the LLM as an already-verified
  fact, so the LLM's role is limited to natural-language synthesis, not
  numeric reasoning.
- **Structured JSON output, not free text** — the report is renderable in a
  UI and could be logged/audited, which free-form prose can't easily support.
- **Separate `/predict`, `/explain`, and `/investigate` endpoints** — the
  first two are fast (pure math); `/investigate` is slower (LLM call), so
  keeping them separate means a live dashboard slider stays responsive.

## API Endpoints

| Endpoint | Description | Speed |
|---|---|---|
| `POST /predict` | Raw fraud probability | Fast |
| `POST /explain` | Probability + SHAP feature contributions | Fast |
| `POST /investigate` | Full pipeline: probability + SHAP + retrieved policy + LLM report | Slower (LLM call) |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install shap sentence-transformers faiss-cpu ollama

# Pull the local LLM
ollama pull llama3.2:3b

# Build the fraud policy vector index (run once, or after editing knowledge_base/)
python build_index.py

# Start the API
uvicorn Fraud:app --reload

# In a separate terminal, start the dashboard
streamlit run app.py
```

## Example Output

```json
{
  "fraud_probability": 0.9859,
  "investigation_report": {
    "risk_level": "high",
    "summary": "This transaction shows a high number of users on this device (4) and elevated trip velocity (6 trips in the last hour), consistent with device-sharing fraud patterns.",
    "matched_fraud_patterns": ["device_sharing_fraud", "velocity_fraud"],
    "recommended_action": "Review the user's account and device activity for connections to other suspicious accounts.",
    "confidence_note": "High confidence based on multiple corroborating risk indicators."
  }
}
```

## Known Limitations

- Fraud pattern definitions and thresholds are a simplified set for
  demonstration purposes, not a production-scale fraud policy.
- The LLM occasionally slightly misattributes *which* specific feature value
  it references in a sentence, even though the underlying risk classification
  is always correct (verified in Python, not by the LLM).
- Real-world fraud systems at scale (e.g. major ride-sharing platforms) also
  incorporate device fingerprinting, geolocation, and cross-user graph
  analysis — this project focuses on the ML explainability + GenAI reporting
  pipeline for a single transaction, not a full production fraud engine.
