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
    # Load the AI pipeline
    ai_engine = JobMatcherPipeline()
    logger.info("AI Engine loaded successfully! Ready to handle requests.")
except Exception as e:
    logger.error(f"Failed to load AI Engine: {e}")
    ai_engine = None

# ==========================================
# 2. AI Helper Functions
# ==========================================

def compose_candidate_bio(data):
    # This function takes dry tags and the 'other' field
    # and turns them into a human-like professional paragraph for the AI to read.
    name = data.get('name', 'המועמד')
    categories = ", ".join(data.get('jobCatagories', []))
    languages = ", ".join(data.get('languages', []))
    licenses = ", ".join(data.get('licenses', []))
    # The real candidate form sends a single free-text "skills" string (e.g.
    # "שירות לקוחות, סבלנות, עבודה עם קופה"), not a "softSkills" array - the
    # array form is kept as a fallback in case some other client ever sends
    # it that way. Without this, the entire skills field was silently
    # dropped from the generated bio.
    raw_skills = data.get('skills', data.get('softSkills', ''))
    skills = ", ".join(raw_skills) if isinstance(raw_skills, list) else str(raw_skills or "")
    software = ", ".join(data.get('software', []))
    other_info = data.get('other', '')
    cv_text = data.get('extracted_cv_text', '')

    original_bio = data.get('bio', '')

    # Building the semantic string in Hebrew
    bio_text = f"פרופיל מקצועי של {name}. "
    
    # CRITICAL FIX - Inject the user's free text bio here!
    if original_bio: 
        bio_text += f"תיאור אישי: {original_bio}. "
        
    if categories: bio_text += f"מעוניין לעבוד בתחומים: {categories}. "
    if languages: bio_text += f"דובר שפות: {languages}. "
    if skills: bio_text += f"כישורים אישיים: {skills}. "
    if software: bio_text += f"שליטה בתוכנות: {software}. "
    if licenses: bio_text += f"רישיונות: {licenses}. "
    if other_info: bio_text += f"מידע נוסף וניסיון: {other_info}. "
    
    # Add a bit of CV text if exists for context
    if cv_text:
        bio_text += f" רקע מקורות חיים: {cv_text[:300]}"
        
    return bio_text.strip()

# ==========================================
# 3. API Routes
# ==========================================

@app.route('/health', methods=['GET'])
def health_check():
    if ai_engine is None:
        return jsonify({"status": "error", "message": "AI Engine failed to load"}), 500
    return jsonify({"status": "healthy", "message": "JobMatcher AI API is running"}), 200

@app.route('/api/generate-bio', methods=['POST'])
def generate_bio():
    """
    New endpoint to create the Bio paragraph before saving to Firestore
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    composed_text = compose_candidate_bio(data)
    return jsonify({"generated_bio": composed_text}), 200

@app.route('/api/match', methods=['POST'])
def predict_match():
    if ai_engine is None:
        return jsonify({"error": "AI Engine is not available"}), 500

    data = request.get_json()

    if not data or 'job' not in data or 'candidate' not in data:
        return jsonify({"error": "Missing job or candidate data"}), 400

    job_json = data['job']
    candidate_json = data['candidate']

    try:
        # The pipeline will use the 'semantic_profile' field
        result = ai_engine.evaluate_candidate(job_json, candidate_json)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)