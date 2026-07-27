## Overview

The **Matching Engine** is an AI-powered service that acts as the core intelligence for **ClickJob**, an app that connects students with short-term, on-demand jobs.

It lives in its own repository, separate from the Android client, and runs as independent **microservices on Google Cloud Run**. Its job is to take a worker's profile (skills, availability, résumé) and compare it against a job's requirements to produce an accurate, ranked list of candidates.

---

## System Architecture

The engine is split into two dedicated services to keep responsibilities clean and allow each side to scale independently:

- **Node.js Backend (The Controller):** The bridge between Firestore and the AI. It listens for matching triggers from the app, fetches the relevant candidate and job data, and applies the initial hard-constraint filtering.
- **Python AI Engine (The Brain):** A Flask service dedicated purely to machine learning and NLP. It receives the pre-filtered candidates, computes match scores, and returns the ranked results.

---

## The Matching Algorithm

Matching runs in two distinct phases, designed for both accuracy and efficiency:

### 1. Hard Constraints Filtering (Node.js)

Candidates who fail a non-negotiable requirement — such as schedule availability or a required license — are **filtered out immediately**, rather than simply receiving a lower cumulative score. This keeps clearly-impossible matches out of the pipeline early, saving compute and keeping the candidate pool relevant before it ever reaches the AI stage.

### 2. AI Scoring & Ranking (Python)

Candidates who pass the hard filters are sent to the AI Engine. It combines unstructured data (résumé text, job descriptions) with structured profile data, using machine learning models to produce a final compatibility score for each candidate.

---

## Tech Stack

| Layer | Tools |
|---|---|
| **Backend** | Node.js with Express |
| **AI Service** | Python with Flask, Scikit-learn, and language models (RoBERTa, SVM) |
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

---

## Key Files Guide

A quick map of where the core logic lives:

**Node.js Backend**
- **`server.js`** — The controller's main entry point: route definitions, the Firebase connection, and outbound communication with the Python server.
- **`src/utils/scheduleMatcher.js`** — Implements the hard-constraint scheduling logic, used to immediately rule out candidates whose availability doesn't fit a job before they're sent to the AI for scoring.
- **`src/controllers/matchController.js`** — Orchestrates the matching flow: fetches candidates and jobs, applies the hard-constraint filters, calls the AI Engine, and saves the ranked matches back to Firestore.
- **`package.json`** — Project configuration, dependencies, and the start script (`npm start`).

**Python AI Engine**
- **`app.py`** — The Flask server's entry point. Receives the filtered candidates, runs the scoring pipeline, and returns the results to Node.js.
- **`final_pipeline.py`** — The core ML/NLP pipeline: loads the fine-tuned models and computes the semantic match between a résumé/profile and a job description.
- **`saved_matching_model/`** — The fine-tuned RoBERTa model used for semantic matching.
- **`svm_feature_extractor.py`** — Feature extraction and scoring logic for the SVM ranking model.
- **`requirements.txt`** — All Python packages required to run the ML engine.

**Configuration & Deployment**
- **`Dockerfile`** — Builds the service container (configured for port 8080) for deployment to Google Cloud Run.
- **`.env`** — Environment variables (not committed to GitHub). Holds the port setting and the AI server's URL.

---

## Team

- Gal Deri
- Netanel Michel
