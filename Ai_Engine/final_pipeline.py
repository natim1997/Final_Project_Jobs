import pandas as pd
import numpy as np
import joblib
import traceback
from sentence_transformers import SentenceTransformer, util

# ==========================================
# Helper Functions for JSON Data
# ==========================================

# Safely convert values to float
def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

# Safely convert values to int
def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

# Ensure value is always a list
def safe_list(val):
    if isinstance(val, list): 
        return val
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, str):
        return [val]
    return []

# ==========================================
# The Main AI Pipeline Class
# ==========================================

class JobMatcherPipeline:
    def __init__(self):
        print("★★★ CLICKJOB AI PIPELINE (VERSION 8.3 - FIXED CASUAL SCORING) ★★★")
        print("Initializing Models...")
        
        try:
            print("1. Loading RoBERTa (Semantic Engine)...")
            self.roberta = SentenceTransformer('./saved_matching_model')
            
            print("2. Loading SVM (The Gatekeeper)...")
            self.svm = joblib.load("./saved_svm_model.pkl")
            
            print("3. Loading MLP (The Final Scorer)...")
            self.mlp = joblib.load("./saved_mlp_model.pkl")
            
            print("Pipeline is fully loaded and READY!\n" + "="*50)
        except Exception as e:
            print(f"CRITICAL ERROR LOADING MODELS: {e}")

    def evaluate_candidate(self, job_json, candidate_json):
        print(f"--> DEBUG: Received Candidate: {candidate_json.get('id', 'unknown')}")
        try:
            # 1. Extract Text Data
            job_description = str(job_json.get("description", ""))
            job_requirements = str(job_json.get("requirements", ""))
            job_text = f"{job_description} {job_requirements}".strip()
            job_category = str(job_json.get("category", "")).strip()

            cand_data = candidate_json.get("candidate", candidate_json) if isinstance(candidate_json.get("candidate"), dict) else candidate_json
            candidate_bio = str(cand_data.get("semantic_profile", "")).strip()
            
            if not candidate_bio:
                candidate_bio = str(cand_data.get("bio", "")).strip()

            candidate_categories = safe_list(cand_data.get("jobCatagories", []))

           # 2. Extract Basic Features
            distance_km = safe_float(cand_data.get("distance_to_job", 5.0))
            search_radius = safe_float(cand_data.get("searchRadius", 50.0)) 
            
            exp_list = cand_data.get("experience", [])
            total_exp_years = sum([safe_int(exp.get("years", 0)) for exp in exp_list if isinstance(exp, dict)])
            experience_months = total_exp_years * 12

            # ==========================================
            # STAGE 0: DEALBREAKERS (Hard Filters)
            # ==========================================
            
            # Reject immediately if the job is outside the user's defined search radius
            if distance_km > search_radius:
                return {
                    "Final_Score": 0.0,
                    "Status": "NO MATCH",
                    "Reason": f"נפסל - מחוץ לרדיוס החיפוש (מרחק: {distance_km} ק״מ, רדיוס מוגדר: {search_radius} ק״מ)",
                    "Breakdown": {
                        "Semantic_Similarity": 0.0,
                        "SVM_Confidence": 0.0,
                        "Experience_Months": experience_months,
                        "Is_Simple_Job": False,
                        "Category_Bonus_Applied": False
                    }
                }
            # ==========================================
            # STAGE 1: Semantic Analysis (RoBERTa)
            # ==========================================
            job_vector = self.roberta.encode(job_text, convert_to_tensor=True)
            candidate_vector = self.roberta.encode(candidate_bio, convert_to_tensor=True)
            
            sim_score = util.cos_sim(job_vector, candidate_vector).item()
            semantic_similarity = max(0.0, min(1.0, sim_score))

            # ==========================================
            # STAGE 2: Gatekeeper Confidence (SVM)
            # ==========================================
            svm_input = pd.DataFrame(
                [[semantic_similarity, distance_km, experience_months]],
                columns=['Semantic_Similarity', 'Distance_km', 'Experience_Months']
            )
            svm_confidence = self.svm.predict_proba(svm_input)[0][1]

            # ==========================================
            # STAGE 3: Base Scoring (MLP)
            # ==========================================
            # FIXED: Sending only the 2 parameters the MLP was trained for!
            mlp_input = pd.DataFrame(
                [[semantic_similarity, svm_confidence]],
                columns=['Semantic_Similarity', 'SVM_Confidence']
            )
            raw_final_score = float(self.mlp.predict(mlp_input)[0])

            # ==========================================
            # STAGE 4: GIG ECONOMY STRICT RANGES & BOOSTS
            # ==========================================
            
            # Define simple job categories for motivation boost (80-88 range)
            simple_categories = [
                "משלוחים ותחבורה", "בעלי חיים", "אפסנאות ולוגיסטיקה", 
                "מסעדנות", "אחזקה", "הפקה ואירועים", 
                "שירות לקוחות", "מכירות ואופנה", "קריאייטיב, עיצוב ומדיה"
            ]

            # Smart category match allowing partial substring matches
            cand_keywords = [word for cat in candidate_categories for word in cat.split()]
            job_keywords = job_category.split()
            category_match = any(kw in job_keywords for kw in cand_keywords)

            is_simple_job = any(cat in job_category for cat in simple_categories)

            # FIXED: We completely trust the new MLP score. No more dividing it by 5 (0.2).
            final_ai_score = raw_final_score

            # ==========================================
            # BUSINESS & UX LOGIC: TARGET RANGES
            # ==========================================
            
            # Motivation Boost for Simple Jobs (Safety Net)
            if is_simple_job and category_match:
                # If it's a simple job and categories match, ensure it never drops below 80
                final_ai_score = max(80.0, final_ai_score)
                # Apply a slight organic boost based on semantic similarity
                final_ai_score += (semantic_similarity * 10.0)
                
            elif is_simple_job and semantic_similarity > 0.05:
                # If they didn't check the category box but the bio matches slightly, give a baseline boost
                final_ai_score = max(65.0, final_ai_score)

            # Strict Ceilings (Never 100%) and Floors
            final_ai_score = min(98.0, max(0.0, final_ai_score))

            # ==========================================
            # STAGE 5: STATUS MAPPING BASED ON EXACT RANGES
            # ==========================================
            
            if final_ai_score < 40.0:
                match_status = "NO MATCH"
                match_reason = "נפסל - ציון נמוך מ-40"
            elif final_ai_score < 60.0:
                match_status = "POOR MATCH"
                match_reason = "לא מתאים - טווח 40-60"
            elif final_ai_score < 70.0:
                match_status = "BASIC MATCH"
                match_reason = "התאמה בסיסית - טווח 60-70"
            elif final_ai_score < 80.0:
                match_status = "GOOD MATCH"
                match_reason = "התאמה טובה - טווח 70-80"
            elif final_ai_score < 90.0:
                match_status = "HIGH MATCH"
                match_reason = "התאמה גבוהה - טווח 80-90 (כולל בוסט למשרות פשוטות)"
            else:
                match_status = "EXCELLENT MATCH"
                match_reason = "התאמה מצוינת - טווח 90-98"
                
            # Final dictionary preparation
            return {
                "Final_Score": round(final_ai_score, 1),
                "Status": match_status,
                "Reason": match_reason,
                "Breakdown": {
                    "Semantic_Similarity": round(semantic_similarity, 3),
                    "SVM_Confidence": round(svm_confidence, 3),
                    "Experience_Months": experience_months,
                    "Is_Simple_Job": is_simple_job,
                    "Category_Bonus_Applied": category_match
                }
            }

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"CRASH CAUGHT: {error_trace}")
            return {
                "Final_Score": 0.0,
                "Status": "REJECTED",
                "Reason": f"PYTHON CRASH: {str(e)}",
                "Breakdown": {}
            }

if __name__ == "__main__":
    print("Run app.py to start the JSON API Server.")