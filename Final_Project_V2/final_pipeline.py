import pandas as pd
import numpy as np
import joblib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# 1. Helper Functions for JSON Data
# ==========================================

def calc_list_match(required_list, candidate_list):
    """Calculates overlap between two JSON lists (like hard skills or languages)."""
    if not required_list: 
        return 1.0 # Perfect match if nothing is required
    
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    matches = req_set.intersection(cand_set)
    return len(matches) / len(req_set)

def check_json_constraint(required_list, candidate_list):
    """Checks mandatory requirements. Returns 1 if all required items exist, else 0."""
    if not required_list: 
        return 1
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    return 1 if req_set.issubset(cand_set) else 0

def calculate_management_bonus(cv_text, job_text, experience_list):
    """
    Check if the candidate has management experience.
    Returns a fractional score (0.0 to 1.0).
    """
    # Simple keywords to find management experience
    management_keywords = ['manager', 'lead', 'head', 'director', 'supervisor', 'מנהל', 'ניהול', 'ראש צוות']
    
    cv_lower = str(cv_text).lower()
    
    # Count how many management words are in the CV
    keyword_matches = sum(1 for word in management_keywords if word in cv_lower)
    
    # Check if the job actually requires a manager
    job_lower = str(job_text).lower()
    job_needs_manager = any(word in job_lower for word in management_keywords)
    
    score = 0.0
    if keyword_matches > 0:
        score += 0.5  # Base bonus for having some management background
        
        # Add more points if they have multiple keywords (up to 0.3 extra)
        score += min(0.3, keyword_matches * 0.1)
        
        # Add bonus if the job specifically asks for a manager
        if job_needs_manager:
            score += 0.2
            
    return round(min(1.0, score), 2)

def calculate_soft_skills_score(cv_text, job_text):
    """
    Extract and match soft skills from the text.
    Returns a fractional score (0.0 to 1.0).
    """
    # Common soft skills to look for
    common_soft_skills = [
        'leadership', 'communication', 'teamwork', 'problem solving', 
        'time management', 'creative', 'flexible', 'customer service',
        'תקשורת', 'עבודת צוות', 'אחריות', 'הגדלת ראש', 'שירותיות'
    ]
    
    cv_lower = str(cv_text).lower()
    job_lower = str(job_text).lower()
    
    # Find which soft skills the job is asking for
    job_requirements = [skill for skill in common_soft_skills if skill in job_lower]
    
    if not job_requirements:
        # If job does not ask for specific soft skills, give an average default
        return 0.5 
        
    # Check how many of the required skills the candidate has
    matched_skills = [skill for skill in job_requirements if skill in cv_lower]
    
    # Calculate percentage (matches / required)
    score = len(matched_skills) / len(job_requirements)
    return round(score, 2)

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
        # 1. Extract raw text for RoBERTa
        job_description_base = job_json.get("description", "")
        job_apparel = " ".join(job_json.get("apparel_requirements", []))
        job_text = f"{job_description_base} {job_apparel}".lower()
        
        cv_text = candidate_json.get("bio", "").lower()

        # 2. Extract Data Nodes
        job_reqs = job_json.get("requirements", {})
        job_basic = job_json.get("basic_info", {})
        
        cand_skills = candidate_json.get("skills", {})
        cand_basic = candidate_json.get("personal_info", {})
        cand_experience_list = candidate_json.get("experience", [])

        # Calculate total experience years
        total_experience_years = sum([exp.get("years", 0) for exp in cand_experience_list if isinstance(exp, dict)])

        # Hard constraint: Check minimum experience
        if total_experience_years < job_reqs.get("min_experience_years", 0):
            return {
                "Final_Score": 0.0,
                "Status": "REJECTED",
                "Reason": "Failed Hard Constraints (Candidate has insufficient experience years)",
                "Breakdown": {
                    "RoBERTa_Score": 0.0,
                    "SVM_Confidence": 0.0,
                    "Hard_Skills_Match": 0.0,
                    "Experience_Bonus": 0.0
                }
            }

        # Flatten technical skills into one list
        cand_hard_skills_pool = cand_skills.get("tech_stack", []) + cand_skills.get("tools", []) + cand_skills.get("certifications", [])

        # 3. Calculate Hard Skills & Languages
        hard_skills_score = calc_list_match(
            job_reqs.get("tech_stack", []) + job_reqs.get("tools", []), 
            cand_hard_skills_pool
        )
        
        languages_score = calc_list_match(
            job_reqs.get("languages", []), 
            cand_skills.get("languages", [])
        )
        
        # Calculate dynamic scores for soft skills and management
        soft_skills_score = calculate_soft_skills_score(cv_text, job_text)
        management_score = calculate_management_bonus(cv_text, job_text, cand_experience_list)

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

            # 5. Calculate SVM Features
            svm_features = {
                "Req_Experience": 1 if total_experience_years >= job_reqs.get("min_experience_years", 0) else 0,
                "Req_Driving": check_json_constraint(job_reqs.get("licenses", []), cand_skills.get("licenses", [])),
                "Req_Security_License": 1, 
                "Req_Gov_License": 1,
                "Req_Student": 1 if job_json.get("dealbreakers", {}).get("is_student_only", False) else 1,
                "Req_Security_Clearance": 1,
                "Req_Finance_Cert": 1,
                "Req_Edu_Sport_Cert": 1,
                "Req_Languages": check_json_constraint(job_reqs.get("languages", []), cand_skills.get("languages", []))
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

        # 6. Extract other features
        location_score = 1.0 if job_basic.get("location_city") == cand_basic.get("city") else 0.0
        work_model_score = 1.0 if job_json.get("dealbreakers", {}).get("is_remote", False) else 0.0

        features = {
            'RoBERTa_Score': round(roberta_score, 4),
            'SVM_Confidence': round(svm_confidence, 4),
            'Hard_Skills_Match': hard_skills_score,
            'Location_Score': location_score,
            'Work_Model_Score': work_model_score,
            'Experience_Bonus': 1.0 if total_experience_years > job_reqs.get("min_experience_years", 0) else 0.0, 
            'Languages_Match': languages_score,
            'Management_Bonus': management_score, 
            'Availability_Score': 1.0, 
            'Mobility_Score': 1.0, 
            'Soft_Skills_Match': soft_skills_score
        }

        # 7. Final Judgment (MLP)
        mlp_input = pd.DataFrame([features])
        final_probs = self.mlp.predict_proba(mlp_input)
        final_score = final_probs[0][1]

        # Heavy penalty if RoBERTa detects a text mismatch
        if roberta_score < 0.05:
            final_score -= 0.45
            final_score = max(0.0, final_score)

        return {
            "Final_Score": round(final_score * 100, 1),
            "Status": "MATCH" if final_score > 0.5 else "NO MATCH",
            "Reason": evaluation_type,
            "Breakdown": features
        }

if __name__ == "__main__":
    print("Run app.py to start the JSON API Server.")