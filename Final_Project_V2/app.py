from flask import Flask, request, jsonify
from final_pipeline import JobMatcherPipeline
import logging

# ==========================================
# 1. Server Setup & Scalability Configuration
# ==========================================

# Configure logging so we can monitor server health
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# SCALABILITY KEY: We initialize the AI Pipeline OUTSIDE the routes.
# This means RoBERTa, SVM, and MLP are loaded into the server's RAM exactly ONE time 
# when the server starts, not every time a user makes a request.
logger.info("Initializing AI Engine... Please wait.")
try:
    ai_engine = JobMatcherPipeline()
    logger.info("AI Engine loaded successfully! Ready to handle requests.")
except Exception as e:
    logger.error(f"Failed to load AI Engine: {e}")
    ai_engine = None

# ==========================================
# 2. API Routes
# ==========================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    A simple endpoint for Google Cloud Run to check if the server is alive.
    """
    if ai_engine is None:
        return jsonify({"status": "error", "message": "AI Engine failed to load"}), 500
    return jsonify({"status": "healthy", "message": "JobMatcher AI API is running"}), 200

@app.route('/api/match', methods=['POST'])
def predict_match():
    """
    The main endpoint for the Node.js server/Android app to send CVs and Job Descriptions.
    Expects a JSON payload.
    """
    if ai_engine is None:
        return jsonify({"error": "AI Engine is not available"}), 500

    # 1. Parse the incoming JSON from the Node.js server
    data = request.get_json()

    # 2. Validate the request (Make sure the Node.js server sent 'job' and 'candidate' objects)
    if not data or 'job' not in data or 'candidate' not in data:
        return jsonify({
            "error": "Invalid request. Please provide 'job' and 'candidate' objects in the JSON body."
        }), 400

    job_json = data['job']
    candidate_json = data['candidate']

    try:
        # 3. Pass the JSON structures to our AI Pipeline
        result = ai_engine.evaluate_candidate(job_json, candidate_json)
        
        # 4. Return the result as a clean JSON to the Node.js server
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Internal server error during prediction"}), 500

# ==========================================
# 3. Local Development Runner
# ==========================================
if __name__ == '__main__':
    # This runs the built-in Flask server for local testing.
    # In production (GCP), Gunicorn will take over and ignore this block.
    app.run(host='0.0.0.0', port=5000, debug=False)