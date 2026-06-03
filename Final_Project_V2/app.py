from flask import Flask, request, jsonify
from final_pipeline import JobMatcherPipeline
import logging

# ==========================================
# 1. Server Setup & Scalability Configuration
# ==========================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info("Initializing AI Engine... Please wait.")
try:
    # simple english comment: Load the AI pipeline (this will load our new version 4.1)
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
    # simple english comment: Check if the server is running without errors
    if ai_engine is None:
        return jsonify({"status": "error", "message": "AI Engine failed to load"}), 500
    return jsonify({"status": "healthy", "message": "JobMatcher AI API is running"}), 200

@app.route('/api/match', methods=['POST'])
def predict_match():
    if ai_engine is None:
        return jsonify({"error": "AI Engine is not available"}), 500

    data = request.get_json()

    # simple english comment: Make sure the request has both job and candidate data
    if not data or 'job' not in data or 'candidate' not in data:
        return jsonify({
            "error": "Invalid request. Please provide 'job' and 'candidate' objects in the JSON body."
        }), 400

    job_json = data['job']
    candidate_json = data['candidate']

    # simple english comment: Log the profile to make sure Node.js sent the data correctly
    semantic_profile = candidate_json.get('semantic_profile', 'No profile found')
    logger.info(f"Received candidate prediction request. Semantic Profile length: {len(semantic_profile)} characters.")

    try:
        # simple english comment: Send the data to our AI model and return the result
        result = ai_engine.evaluate_candidate(job_json, candidate_json)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Internal server error during prediction"}), 500

# ==========================================
# 3. Local Development Runner
# ==========================================
if __name__ == '__main__':
    # simple english comment: Start the local server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)