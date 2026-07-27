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

- **Node.js Backend (The Controller):** The bridge between Firestore and the AI. It listens for matching triggers from the app, fetches the relevant candidate and job data, and applies the initial hard-constraint filtering.
- **Python AI Engine (The Brain):** A Flask service dedicated purely to machine learning and NLP. It receives the pre-filtered candidates, computes match scores, and returns the ranked results.

---

## The Matching Algorithm

Matching runs in two distinct phases, designed for both accuracy and efficiency:

### 1. Hard Constraints Filtering (Node.js)

Candidates who fail a non-negotiable requirement — such as schedule availability or a required license — are **filtered out immediately**, rather than simply receiving a lower cumulative score. This keeps clearly-impossible matches out of the pipeline early, saving compute power and keeping the candidate pool relevant before it ever reaches the AI stage.

### 2. AI Scoring & Ranking (Python)

Candidates who pass the hard filters are sent to the AI Engine. It combines unstructured data (résumé text, job descriptions) with structured profile data, using machine learning models to produce a final compatibility score for each candidate.

---

## The Machine Learning Pipeline & Models

To accurately score and rank candidates, the Python AI Engine executes a multi-step machine learning pipeline:

- **PDF Parsing & Data Extraction:** When a user uploads a résumé, the backend extracts the raw text from the PDF, pulling unstructured information that represents the user's background and experience.
- **Semantic Matching (RoBERTa):** A fine-tuned RoBERTa model processes the text from both the job description and the candidate's parsed résumé. It generates contextual embeddings to calculate semantic similarity, understanding the *meaning* behind the text rather than just performing basic keyword matching.
- **Feature Engineering:** The semantic similarity scores extracted from the NLP layer are combined with structured data (e.g., direct skill overlaps) into a comprehensive feature vector.
- **Scoring Models (SVM & MLP):** The final feature vectors are fed into classification models to predict the match probability. The system uses both a Support Vector Machine (SVM) and a Multi-Layer Perceptron (MLP) neural network to weigh the extracted features and generate the definitive ranking score.

---

## Model Training & Evaluation

To ensure high accuracy in predicting job matches, the models underwent a rigorous training process:

- **Data Preparation:** The models were trained on a carefully curated dataset of job descriptions and candidate profiles, labeled for compatibility.
- **Fine-Tuning:** The base RoBERTa model was fine-tuned specifically on domain-relevant employment data to better capture industry-specific terminology and context.
- **Evaluation:** The classification models (SVM and MLP) were trained and validated on split datasets, and evaluated using key metrics such as accuracy, precision, and recall — ensuring the final ranking is robust, reliable, and free from heavy biases.

---

## Tech Stack

| Layer | Tools |
|---|---|
| **Backend** | Node.js with Express |
| **AI Service** | Python with Flask, Scikit-learn, and NLP models (RoBERTa, SVM, MLP) |
| **Database & Auth** | Firebase Admin SDK working against Firestore |
| **Cloud & Runtime** | Docker and Google Cloud Run |

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

**2. Run the Node.js Backend**

```bash
# Navigate to the Node.js directory
cd Node_Backend

# Install packages
npm install

# Create a .env file with the port, the AI server URL, and Firebase credentials
echo "PORT=8080" > .env

# Start the server
npm start
```

> ⚠️ &nbsp;`AI_SERVER_URL` must point to the Python engine **including its route path** (e.g. `http://127.0.0.1:5000/api/match` locally, or `https://<your-cloud-run-url>/api/match` in production) — the base URL alone will return a 404.

---

## Key Files Guide

A quick map of where the core logic lives:

**Node.js Backend**
- **`server.js`** — The controller's main entry point: route definitions, the Firebase connection, and outbound communication with the Python server.
- **`src/utils/scheduleMatcher.js`** — Implements the hard-constraint scheduling logic, used to immediately rule out candidates whose availability doesn't fit a job before they're sent to the AI for scoring.
- **`src/controllers/matchController.js`** — Orchestrates the matching flow: fetches candidates and jobs, applies the hard-constraint filters, calls the AI Engine, and saves the ranked matches back to Firestore.
- **`src/services/aiService.js`** — Handles the outbound request to the Python AI Engine and normalizes its response for the rest of the backend.
- **`package.json`** — Project configuration, dependencies, and the start script (`npm start`).

**Python AI Engine**
- **`app.py`** — The Flask server's entry point. Receives the filtered candidates, runs the scoring pipeline, and returns the results to Node.js.
- **`final_pipeline.py`** — The core ML/NLP pipeline: loads the fine-tuned models (RoBERTa and MLP) and computes the semantic match between a résumé/profile and a job description.
- **`svm_feature_extractor.py`** — Feature extraction and scoring logic for the SVM ranking model.
- **`saved_matching_model/`** — The fine-tuned RoBERTa model used for semantic matching.
- **`saved_svm_model.pkl`** / **`saved_mlp_model.pkl`** — The trained SVM and MLP classifiers used for final match scoring.
- **`requirements.txt`** — All Python packages required to run the ML engine.

**Configuration & Deployment**
- **`Dockerfile`** — Builds the service container (configured for port 8080) for deployment to Google Cloud Run.
- **`.env`** — Environment variables (not committed to GitHub). Holds the port setting and the AI server's URL.

---

## Team

- Gal Deri
- Netanel Michel
