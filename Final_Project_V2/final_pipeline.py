import pandas as pd
import numpy as np
import joblib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# 1. Helper Functions for JSON Data
# ==========================================

def calc_list_match(required_list, candidate_list):
    """Calculates overlap between two JSON lists (e.g., hard skills, languages)."""
    if not required_list: 
        return 1.0 # If nothing is required, it's a perfect match
    
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    matches = req_set.intersection(cand_set)
    return len(matches) / len(req_set)

def check_json_constraint(required_list, candidate_list):
    """For mandatory requirements (like SVM). If required is missing in candidate, returns 0."""
    if not required_list: 
        return 1
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    # Returns 1 only if all required items are in the candidate's list
    return 1 if req_set.issubset(cand_set) else 0

# ==========================================
# 2. Pipeline Manager Class
# ==========================================

class JobMatcherPipeline:
    def __init__(self):
        print("Initializing AI Pipeline...")
        print("1. Loading RoBERTa (Semantic Engine)...")
        model_path = "./saved_matching_model"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.roberta = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.roberta.eval()
        
        print("2. Loading SVM (The Gatekeeper)...")
        self.svm = joblib.load("Models/svm_model.pkl")
        
        print("3. Loading MLP (The Meta-Learner)...")
        self.mlp = joblib.load("Models/mlp_model.pkl")
        print("Pipeline is READY!\n" + "="*40)

    def evaluate_candidate(self, job_json, candidate_json):
        # 1. Extract raw text for RoBERTa by combining text fields
        job_text = " ".join(job_json.get("text_fields", {}).values()).lower()
        cv_text = " ".join(candidate_json.get("text_fields", {}).values()).lower()

        # 2. Extract Data Nodes
        job_reqs = job_json.get("requirements", {})
        cand_skills = candidate_json.get("experience_and_skills", {})
        
        job_basic = job_json.get("basic_info", {})
        cand_basic = candidate_json.get("personal_info", {})

        # 3. Calculate Hard Skills & Languages using JSON Lists
        hard_skills_score = calc_list_match(
            job_reqs.get("required_hard_skills", []), 
            cand_skills.get("hard_skills", [])
        )
        
        languages_score = calc_list_match(
            job_reqs.get("required_languages", []), 
            cand_skills.get("languages", [])
        )
        
        soft_skills_score = calc_list_match(
            job_reqs.get("required_soft_skills", []), 
            cand_skills.get("soft_skills", [])
        )

        # 4. Fallback Logic for Short Text
        word_count = len(cv_text.split()) + len(job_text.split())
        if word_count < 25:
            roberta_score = hard_skills_score
            evaluation_type = "Fallback Mode (JSON Keyword based due to short text)"
        else:
            inputs = self.tokenizer(job_text, cv_text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.roberta(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                roberta_score = probs[0][1].item()
            evaluation_type = "Deep Semantic Mode (Full RoBERTa analysis)"

        # 5. Calculate SVM Features (Using the pre-trained structure)
        # We simulate the 9 SVM fields by checking mandatory JSON lists.
        # This makes the SVM MUCH more accurate than regex!
        svm_features = {
            "Req_Experience": 1 if cand_skills.get("total_experience_years", 0) >= job_reqs.get("min_experience_years", 0) else 0,
            "Req_Driving": check_json_constraint(job_reqs.get("mandatory_licenses", []), cand_skills.get("licenses_and_certs", [])),
            "Req_Security_License": 1, # Defaulting unused old constraints to 1 to keep SVM happy
            "Req_Gov_License": 1,
            "Req_Student": 1 if job_reqs.get("required_education", "") == cand_basic.get("education_level", "") else 0,
            "Req_Security_Clearance": 1,
            "Req_Finance_Cert": 1,
            "Req_Edu_Sport_Cert": 1,
            "Req_Languages": check_json_constraint(job_reqs.get("required_languages", []), cand_skills.get("languages", []))
        }
        
        svm_input = pd.DataFrame([svm_features])
        svm_probs = self.svm.predict_proba(svm_input)
        svm_confidence = svm_probs[0][1]

        if svm_confidence < 0.15:
            return {
                "Final_Score": 0.0,
                "Status": "REJECTED",
                "Reason": "Failed Hard Constraints (JSON: Missing mandatory license or experience)",
                "SVM_Confidence": round(svm_confidence * 100, 1)
            }

        # 6. Extract the rest of the MLP Soft Constraints
        location_score = 1.0 if job_basic.get("location_city") == cand_basic.get("location_city") else 0.0
        work_model_score = 1.0 if job_basic.get("work_model") == candidate_json.get("availability_and_schedule", {}).get("work_model_preference") else 0.0

        features = {
            'RoBERTa_Score': round(roberta_score, 4),
            'SVM_Confidence': round(svm_confidence, 4),
            'Hard_Skills_Match': hard_skills_score,
            'Location_Score': location_score,
            'Work_Model_Score': work_model_score,
            'Experience_Bonus': 1.0 if cand_skills.get("total_experience_years", 0) > job_reqs.get("min_experience_years", 0) else 0.0, 
            'Education_Score': 1.0, 
            'Languages_Match': languages_score,
            'Management_Bonus': 1.0, 
            'Military_Bonus': 1.0, 
            'Availability_Score': 1.0, 
            'Mobility_Score': 1.0 if cand_basic.get("mobility", {}).get("has_car") else 0.0, 
            'Soft_Skills_Match': soft_skills_score
        }

        # 7. The Meta-Learner (MLP) Final Judgment
        mlp_input = pd.DataFrame([features])
        final_probs = self.mlp.predict_proba(mlp_input)
        final_score = final_probs[0][1]

        return {
            "Final_Score": round(final_score * 100, 1),
            "Status": "MATCH" if final_score > 0.5 else "NO MATCH",
            "Reason": evaluation_type,
            "Breakdown": features
        }

if __name__ == "__main__":
    print("Run app.py to start the JSON API Server.")