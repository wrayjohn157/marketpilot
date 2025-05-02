# 🧠 ML Model Outsourcing Options for Trade Log Data

This document outlines paid and free options for outsourcing the training of ML models (e.g., `recovery_odds`, `confidence_score`) using your crypto trade logs.

---

## 👷‍♂️ Freelance / Consultant Options (Human-Guided Training)

### 1. **Upwork**
- **Best for:** Custom trade prediction logic, cost-effective help
- **Cost:** $25–$75/hr; or $400–$1500 per project
- **Deliverables:** XGBoost or PyTorch/Sklearn models, notebook, exportable `.pkl` files
- **Tips:** Filter for skills like `AutoML`, `XGBoost`, `cryptocurrency`, `model deployment`

**Sample Title:**  
*“Train XGBoost Confidence Model Using Crypto Trading Logs (JSONL Format)”*

---

### 2. **Toptal / Turing**
- **Best for:** Production-grade modeling with high reliability and clean code
- **Cost:** $80–$200/hr; $2000–$8000 total typical range
- **Pro:** NDA-friendly, enterprise level delivery
- **Con:** Overkill for early testing unless you’re scaling

---

### 3. **Aragon AI / Latent Space**
- **Best for:** Done-for-you ML model pipelines
- **Cost:** $1500–$5000 fixed project cost
- **Deliverables:** Preprocessed datasets, trained models, prediction APIs or exports

---

## ⚙️ AutoML Platforms (Upload & Train, No Code Required)

### 4. **Google Vertex AI AutoML Tables**
- **Best for:** Scalable training with easy export
- **Free tier:** 10 node-hours/month
- **Paid:** $2–$5/hour training after free quota
- **Supports:** CSV upload, model export (TensorFlow, ONNX)
- **URL:** https://cloud.google.com/vertex-ai

---

### 5. **BigML**
- **Best for:** Simple UI + JSON upload + batch predictions
- **Free tier:** Small datasets
- **Paid:** $30–$100/month
- **Export:** PMML, downloadable trees, or batch prediction UI
- **URL:** https://bigml.com

---

### 6. **Akkio**
- **Best for:** Business users wanting quick live models
- **Free trial:** Yes
- **Paid:** Starts at $49/month
- **Output:** API endpoints only (no `.pkl` export)
- **URL:** https://akkio.com

---

## 💡 Suggested Workflow

| Step | Action |
|------|--------|
| ✅ 1 | Use **BigML** or **Vertex AI AutoML** to upload logs and train initial models |
| ✅ 2 | Compare predictions with your internal system for validation |
| ✅ 3 | If performance is weak, hire via **Upwork** or **Aragon AI** |
| 🧠 4 | For scaling, formalize logs into a versioned dataset and re-train monthly |

---

## 📌 Extras

- For notebooks and exportable `.pkl` models, **freelancers** are typically better.
- For real-time deployment via API, **Akkio** or **Vertex AI** are good.
- For high-trust environments (e.g., production bots), use **Toptal** or self-hosted pipelines.
