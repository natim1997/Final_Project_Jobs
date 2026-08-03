<div align="center">

# ClickJob - AI Matching Engine 🧠

**The intelligence layer behind ClickJob — pairing students with short-term, on-demand jobs**

![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![Express](https://img.shields.io/badge/Express-000000?style=for-the-badge&logo=express&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![Google Cloud Run](https://img.shields.io/badge/Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)

</div>

The Matching Engine is an AI-powered service that acts as the core intelligence for **ClickJob**, an app that connects students with short-term, on-demand jobs.

It lives in its own repository, separate from the Android client, and runs as independent **microservices on Google Cloud Run**. Its job is to take a worker's profile (skills, availability, résumé) and compare it against a job's requirements to produce an accurate, ranked list of candidates.

> 📱 &nbsp;The Android client and overall product experience live in a separate repository → **[ClickJob App](https://github.com/galDeri23/ClickJob_FinalProject)**

---

## System Architecture

The engine is split into two dedicated services to keep responsibilities clean and allow each side to scale independently:

- **Node.js Backend (The Controller):** The bridge between Firestore and the AI. It listens for matching triggers from the app, fetches the relevant candidate and job data, and applies the initial hard-constraint filtering. Note: schedule filtering currently only runs on the candidate-facing flow (`getMatchesForCandidate`) - the employer-facing flow (`getJobCandidates`) does not yet apply it.
- **Python AI Engine (The Brain):** A Flask service dedicated to machine learning, NLP, and business-rule scoring. It runs its own gatekeeper checks, then scores and ranks the candidates who pass.

---

## The Matching Algorithm

Matching runs in three phases, designed for both accuracy and efficiency:

### 1. Hard Constraints Filtering (Node.js)

Candidates who fail a non-negotiable requirement — such as schedule availability or a required license — are **filtered out immediately**, rather than simply receiving a lower cumulative score. This keeps clearly-impossible matches out of the pipeline early, saving compute power before a request ever reaches the AI stage.

### 2. The Gatekeeper (Python)

Before any scoring happens, the AI Engine runs its own hard checks on the pair: is the job within the candidate's search radius, does the candidate's profile actually read like a job seeker (not an employer), did they explicitly rule out this kind of work, and does the candidate show any sign of meeting a required credential (license/certification)? A failure at this stage returns a score of `0` immediately, with no further scoring.

### 3. AI Scoring & Ranking (Python)

Candidates who pass the gatekeeper are scored on two combined dimensions: a **Semantic & Experience Matcher** (60% weight — how relevant is this candidate's background to this specific job, via a hybrid of a pretrained multilingual RoBERTa embedding model and classic TF-IDF keyword matching, weighted equally) and a **Motivation & Soft-Skill Booster** (40% weight — transferable skills like responsibility and reliability, with an extra floor for casual/entry-level job categories so a lack of direct experience doesn't unfairly tank an otherwise promising candidate). The result is rescaled onto a 0–100 display range (calibrated against real candidate/job pairs) and mapped to a human-readable match tier. SVM and MLP models still run and contribute to the diagnostic breakdown returned by the API, but do not currently determine the final score - see the engineering report for why.

---

## The Machine Learning Pipeline & Models

To accurately score and rank candidates, the Python AI Engine executes a multi-step machine learning pipeline:

- **PDF Parsing & Data Extraction:** When a user uploads a résumé, the backend extracts the raw text from the PDF, pulling unstructured information that represents the user's background and experience.
- **Semantic Matching (RoBERTa + TF-IDF):** A pretrained multilingual RoBERTa model (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, loaded from the Hugging Face Hub) generates contextual embeddings for both the job description and the candidate's parsed résumé to calculate semantic similarity. This is combined in an equal-weight hybrid with a classic TF-IDF keyword score, which catches exact-term matches (e.g. a specific tool or license name) that pure semantic similarity can sometimes miss.
- **Feature Engineering:** The semantic similarity score is combined with structured signals (SVM confidence, stated experience, transferable soft skills) into a feature set for the scoring models.
- **Scoring Models (SVM & MLP):** An SVM produces a confidence signal and an MLP combines it with semantic similarity into a supplementary relevance signal, both surfaced in the API's diagnostic breakdown - the current final score is computed directly from the RoBERTa+TF-IDF hybrid similarity, per findings documented in the engineering report.
- **Business-Rule Layer (Gatekeeper & Motivation Booster):** On top of the ML models, an explicit rules layer disqualifies clear non-matches (wrong persona, explicit refusal, missing required credential) and boosts soft-skill/motivation signals for casual job categories, so a candidate isn't penalized purely for lacking direct industry experience in an entry-level role.

---

## Model Training & Evaluation

To measure and improve accuracy in predicting job matches, the models went through a rigorous evaluation process:

- **Data Preparation:** The models were trained on a curated dataset of real job postings and candidate profiles, labeled for compatibility.
- **Fine-tuning tried and reverted:** An earlier iteration fine-tuned the RoBERTa model on synthetic, English-only training data. Head-to-head testing against real job postings showed this actually *hurt* accuracy relative to the plain pretrained model, so the fine-tuned version was dropped in favor of the base pretrained model - see the engineering report for the full comparison.
- **Evaluation:** The classification models (SVM and MLP) were trained and validated on held-out data, and evaluated using metrics such as accuracy, precision, and recall. The measured end-to-end Precision@5 (~0.37, up from a 0.10 baseline) is below the 85% target originally set for this project. Root-cause analysis across seven independent approaches points to the automatic category-based labeling method (not model choice) as the limiting factor - closing that gap requires human-verified relevance labels, not further model tuning. Full methodology, numbers, and honest limitations are in the engineering report.

---

## Tech Stack

- **Backend:** Node.js with Express
- **AI Service:** Python with Flask, Scikit-learn, Sentence-Transformers (RoBERTa), scikit-learn TF-IDF, and SVM/MLP models
- **Database & Auth:** Firebase Admin SDK working against Firestore
- **Cloud & Runtime:** Docker and Google Cloud Run

---

## Getting Started

**Prerequisites:** Node.js (v18+), Python (3.11+), and a Firebase service account key (`serviceAccountKey.json`).

**1. Run the AI Engine (Python)**

```bash
# Navigate to the Python directory
cd Ai_Engine

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

> ⚠️ &nbsp;On Windows, running `python app.py` directly can silently fail to load the AI engine - the console's default codepage can't print a Unicode character in a startup log line, which crashes model loading before it starts (the server still comes up, but every request returns "AI Engine is not available"). Set UTF-8 mode first: `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING="utf-8"` (PowerShell), then run `python app.py`. This doesn't affect Docker/Cloud Run.

**2. Run the Node.js Backend**

```bash
# Navigate to the Node.js directory
cd Node_Backend

# Install packages
npm install

# Create a .env file (see below for required keys)
touch .env

# Start the server
npm start
```

Your `.env` needs:

```env
PORT=8080
AI_SERVER_URL=http://127.0.0.1:5000
```

> ⚠️ &nbsp;`AI_SERVER_URL` is the Python engine's **base URL only** — no route path (e.g. `http://127.0.0.1:5000` locally, or your Cloud Run URL in production). The Node backend appends `/api/match` and `/api/generate-bio` itself; including the path here will produce a broken double-path URL.

Firebase credentials come from a service account key file, not an env var: generate one from Firebase Console → Project Settings → Service Accounts → Generate New Private Key, and place it as `serviceAccountKey.json` in `Node_Backend/src/config/` for local development (see `serviceAccountKey.example.json` in that folder for the expected shape - never commit the real file). In Cloud Run, this is skipped in favor of the service's default credentials automatically.

---

## Key Files Guide

A quick map of where the core logic lives:

**Node.js Backend**
- **`server.js`** — The controller's main entry point: middleware, route registration, and the Firebase connection.
- **`src/utils/scheduleMatcher.js`** — Implements the hard-constraint scheduling logic, used to immediately rule out candidates whose availability doesn't fit a job before they're sent to the AI for scoring.
- **`src/controllers/matchController.js`** — Orchestrates the matching flow for a candidate: fetches candidates and jobs, applies the hard-constraint filters, calls the AI Engine, and saves the ranked matches back to Firestore.
- **`src/controllers/jobController.js`** — Employer-side job management (create/update/delete), and `getJobCandidates`, which runs the same AI-scoring flow in reverse to list matching candidates for a given job.
- **`src/utils/matchCalculator.js`** — Shared city-based distance calculation (used by both controllers to build the AI payload) plus the final location gate and match status.
- **`src/services/aiService.js`** — Handles the outbound request to the Python AI Engine and normalizes its response for the rest of the backend.
- **`src/controllers/candidateController.js`** — Handles candidate profile creation/updates, including PDF résumé parsing (via `pdf-parse`) before the extracted text is sent onward for AI scoring. A dedicated `/api/extract-cv` route in `server.js` also exposes this extraction on its own.
- **`package.json`** — Project configuration, dependencies, and the start script (`npm start`).

**Python AI Engine**
- **`app.py`** — The Flask server's entry point. Composes candidate bios (`/api/generate-bio`) and runs the scoring pipeline (`/api/match`).
- **`final_pipeline.py`** — The core pipeline: the Gatekeeper hard-check stage, RoBERTa+TF-IDF hybrid semantic similarity, the SVM/MLP diagnostic models, the display-score rescaling and relevance-gated labeling, and the soft-skill/motivation scoring.
- **`saved_tfidf_vectorizer.pkl`** — The fitted TF-IDF vectorizer used for the keyword-matching half of the semantic score.
- **`saved_svm_model_v2.pkl`** / **`saved_mlp_model_v2.pkl`** — The SVM and MLP classifiers, retrained on real (not synthetic) job data; used for the diagnostic breakdown, not the current final score.
- **`requirements.txt`** — All Python packages required to run the ML engine.

The RoBERTa embedding model itself isn't stored in this repo - it's downloaded on startup from the Hugging Face Hub (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`).

**Configuration & Deployment**
- **`Dockerfile`** — Builds the service container (configured for port 8080) for deployment to Google Cloud Run.
- **`.env`** — Environment variables (not committed to GitHub). Holds the port setting and the AI server's URL.

---

## Team

- Gal Deri
- Netanel Michel

