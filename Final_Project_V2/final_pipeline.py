import pandas as pd
import numpy as np
import joblib
import torch
import traceback
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# 1. Helper Functions for JSON Data (Bulletproof)
# ==========================================

# simple english comment: Ensure we always get a valid list, even if Firebase sends dict or null
def safe_list(val):
    if isinstance(val, list): 
        return val
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, str):
        return [val]
    return []

# simple english comment: Ensure we always get a valid number
def safe_int(val):
    try:
        return int(val)
    except:
        return 0

def calc_list_match(required_list, candidate_list):
    # simple english comment: Calculates overlap between two lists
    if not required_list: 
        return 1.0
    
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    matches = req_set.intersection(cand_set)
    return len(matches) / len(req_set)

def check_json_constraint(required_list, candidate_list):
    # simple english comment: Checks mandatory requirements. Returns 1 if all exist
    if not required_list: 
        return 1
    req_set = set([str(x).lower() for x in required_list])
    cand_set = set([str(x).lower() for x in candidate_list])
    
    return 1 if req_set.issubset(cand_set) else 0

def calculate_management_bonus(cv_text, job_text, experience_list):
    # simple english comment: Check if candidate has management experience
    management_keywords = ['manager', 'lead', 'head', 'director', 'supervisor', 'מנהל', 'ניהול', 'ראש צוות']
    
    cv_lower = str(cv_text).lower()
    
    keyword_matches = sum(1 for word in management_keywords if word in cv_lower)
    job_lower = str(job_text).lower()
    job_needs_manager = any(word in job_lower for word in management_keywords)
    
    score = 0.0
    if keyword_matches > 0:
        score += 0.5  # simple english comment: Base bonus
        score += min(0.3, keyword_matches * 0.1) # simple english comment: Extra points
        if job_needs_manager:
            score += 0.2
            
    return round(min(1.0, score), 2)

def calculate_soft_skills_score(cv_text, job_text):
    # simple english comment: Extract and match soft skills
    common_soft_skills = [
        'leadership', 'communication', 'teamwork', 'problem solving', 
        'time management', 'creative', 'flexible', 'customer service',
        'תקשורת', 'עבודת צוות', 'אחריות', 'הגדלת ראש', 'שירותיות'
    ]
    
    cv_lower = str(cv_text).lower()
    job_lower = str(job_text).lower()
    
    job_requirements = [skill for skill in common_soft_skills if skill in job_lower]
    
    if not job_requirements:
        return 0.5 
        
    matched_skills = [skill for skill in job_requirements if skill in cv_lower]
    return round(len(matched_skills) / len(job_requirements), 2)

def calc_list_match_robust(required_list, candidate_json_raw):
    # simple english comment: Convert entire JSON to string to guarantee we find the skills anywhere
    if not required_list: 
        return 1.0
    
    cand_str = str(candidate_json_raw).lower()
    req_set = set([str(x).lower() for x in required_list])
    
    matches = [req for req in req_set if req in cand_str]
    return len(matches) / len(req_set)

# ==========================================
# 2. Pipeline Manager Class
# ==========================================

class JobMatcherPipeline:
    def __init__(self):
        print("★★★ NEW PIPELINE VERSION 4.7 (CASUAL JOBS MOTIVATION LOGIC) LOADED ★★★")
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
        # simple english comment: Massive Try-Catch block to prevent 500 errors and catch exactly what goes wrong
        try:
            # 1. Extract raw text for RoBERTa
            job_description_base = str(job_json.get("description", ""))
            job_apparel = " ".join(safe_list(job_json.get("apparel_requirements")))
            job_text = f"{job_description_base} {job_apparel}".lower()
            
            # simple english comment: Safely extract nested candidate data
            cand_data = candidate_json.get("candidate", candidate_json) if isinstance(candidate_json.get("candidate"), dict) else candidate_json
            cv_text = str(cand_data.get("semantic_profile", cand_data.get("bio", ""))).lower()

            # 2. Extract Data Nodes
            job_reqs = job_json.get("requirements") or {}
            job_basic = job_json.get("basic_info") or {}
            job_deals = job_json.get("dealbreakers") or {}
            
            cand_skills = cand_data.get("skills") or {}
            cand_basic = cand_data.get("personal_info") or {}
            cand_experience_list = safe_list(cand_data.get("experience"))

            # simple english comment: Calculate total experience years safely
            total_experience_years = sum([safe_int(exp.get("years", 0)) for exp in cand_experience_list if isinstance(exp, dict)])
            job_min_experience = safe_int(job_reqs.get("min_experience_years", 0))

            # simple english comment: Hard constraint check (Basic validation)
            if len(cv_text) < 100 and total_experience_years < job_min_experience:
                return {
                    "Final_Score": 0.0,
                    "Status": "REJECTED",
                    "Reason": "Failed Hard Constraints (Insufficient manual experience and no CV provided)",
                    "Breakdown": { "RoBERTa_Score": 0.0, "SVM_Confidence": 0.0, "Hard_Skills_Match": 0.0, "Experience_Bonus": 0.0 }
                }

            # simple english comment: Flatten technical skills for required list only
            job_hard_skills_reqs = safe_list(job_reqs.get("tech_stack")) + safe_list(job_reqs.get("tools"))

            # 3. Calculate Hard Skills & Languages USING ROBUST STRING SEARCH
            hard_skills_score = calc_list_match_robust(job_hard_skills_reqs, candidate_json)
            languages_score = calc_list_match_robust(safe_list(job_reqs.get("languages")), candidate_json)
            
            # simple english comment: Calculate dynamic scores
            soft_skills_score = calculate_soft_skills_score(cv_text, job_text)
            management_score = calculate_management_bonus(cv_text, job_text, cand_experience_list)

            # 4. Fallback Logic for Short Text & RoBERTa Score
            word_count = len(cv_text.split()) + len(job_text.split())
            if word_count < 25:
                roberta_score = float(hard_skills_score)
                evaluation_type = "Fallback Mode (JSON Keyword based due to short text)"
            else:
                inputs = self.tokenizer(job_text, cv_text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.roberta(**inputs)
                    # simple english comment: Use softmax because the model is trained for classification
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    roberta_score = float(probs[0][1].item())
                evaluation_type = "Deep Semantic Classification"

            # 5. Calculate SVM Features safely
            svm_features = {
                "Req_Experience": 1 if (total_experience_years >= job_min_experience or len(cv_text) >= 100) else 0,
                "Req_Driving": check_json_constraint(safe_list(job_reqs.get("licenses")), safe_list(cand_skills.get("licenses"))),
                "Req_Security_License": 1, 
                "Req_Gov_License": 1,
                "Req_Student": 1 if job_deals.get("is_student_only", False) else 1,
                "Req_Security_Clearance": 1,
                "Req_Finance_Cert": 1,
                "Req_Edu_Sport_Cert": 1,
                "Req_Languages": check_json_constraint(safe_list(job_reqs.get("languages")), safe_list(cand_skills.get("languages")))
            }
            
            svm_input = pd.DataFrame([svm_features])
            svm_probs = self.svm.predict_proba(svm_input)
            svm_confidence = float(svm_probs[0][1])

            if svm_confidence < 0.15:
                return {
                    "Final_Score": 0.0,
                    "Status": "REJECTED",
                    "Reason": "Failed SVM Verification (Missing mandatory JSON logic)",
                    "SVM_Confidence": round(svm_confidence * 100, 1)
                }

            # 6. Extract other features
            location_score = 1.0 if str(job_basic.get("location_city")) == str(cand_basic.get("city")) else 0.0
            work_model_score = 1.0 if job_deals.get("is_remote", False) else 0.0

            features = {
                'RoBERTa_Score': round(roberta_score, 4),
                'SVM_Confidence': round(svm_confidence, 4),
                'Hard_Skills_Match': float(hard_skills_score),
                'Location_Score': location_score,
                'Work_Model_Score': work_model_score,
                'Experience_Bonus': 1.0 if (total_experience_years > job_min_experience or len(cv_text) >= 100) else 0.0, 
                'Languages_Match': float(languages_score),
                'Management_Bonus': float(management_score), 
                'Availability_Score': 1.0, 
                'Mobility_Score': 1.0, 
                'Soft_Skills_Match': float(soft_skills_score)
            }

            # 7. Final Judgment (MLP)
            mlp_input = pd.DataFrame([features])
            final_probs = self.mlp.predict_proba(mlp_input)
            mlp_base_score = float(final_probs[0][1])

            if roberta_score < 0.05:
                mlp_base_score -= 0.45
                mlp_base_score = max(0.0, mlp_base_score)

            # ==========================================
            # REALISTIC SCORING LOGIC V4.7 (GIG ECONOMY ADAPTATION)
            # ==========================================
            
            cv_words = set([w.strip(',.') for w in cv_text.split() if len(w) > 3])
            job_words = set([w.strip(',.') for w in job_text.split() if len(w) > 3])
            overlap_count = len(cv_words.intersection(job_words))
            
            is_tech_job = len(job_hard_skills_reqs) > 0
            
            if is_tech_job and float(hard_skills_score) < 0.3:
                # simple english comment: KILL SWITCH - Crush the score for tech jobs if skills don't match
                raw_ai_score = roberta_score * 25.0
                variance_multiplier = 0.0 
            
            elif not is_tech_job:
                # simple english comment: Casual jobs (no tech stack). Goal: Motivate people to apply (80-90 range)
                base_score = 78.0 
                semantic_bonus = roberta_score * 8.0
                soft_bonus = float(soft_skills_score) * 4.0
                
                # simple english comment: Experience only helps and gives a bonus (+3 points)
                exp_bonus = 3.0 if total_experience_years > 0 else 0.0
                
                raw_ai_score = base_score + semantic_bonus + soft_bonus + exp_bonus
                
                # simple english comment: Cap casual jobs at 92 max to reserve 93+ for perfect tech matches
                raw_ai_score = min(92.0, raw_ai_score)
                variance_multiplier = 1.0
                
            else:
                # simple english comment: Tech jobs where the candidate actually has the skills
                base_score = (float(hard_skills_score) * 40) + (roberta_score * 40) + (float(soft_skills_score) * 20)
                word_bonus = min(overlap_count, 10) * 1.0 # simple english comment: max 10 points
                raw_ai_score = base_score + word_bonus
                variance_multiplier = 1.0 + (word_bonus / 100)
                
            # simple english comment: Add a tiny mathematical jitter
            jitter = (len(job_text) % 5) * 0.3 
            raw_ai_score += jitter

            # simple english comment: Cap the overall score
            human_score = max(12.0, min(99.0, raw_ai_score))

            # simple english comment: Dynamic Status based on the sensitive score
            if human_score >= 80:
                final_status = "MATCH"
            elif human_score >= 60:
                final_status = "POTENTIAL"
            else:
                final_status = "NO MATCH"

            return {
                "Final_Score": round(human_score, 1),
                "Status": final_status,
                "Reason": evaluation_type,
                "Breakdown": features
            }

        except Exception as e:
            # simple english comment: Catch ANY error and send it back to Postman instead of crashing the server
            error_trace = traceback.format_exc()
            print(f"CRASH CAUGHT: {error_trace}")
            return {
                "Final_Score": 0.0,
                "Status": "REJECTED",
                "Reason": f"PYTHON CRASH: {str(e)}",
                "Breakdown": { "Error_Details": "Check terminal for full traceback" }
            }

if __name__ == "__main__":
    print("Run app.py to start the JSON API Server.")