import pandas as pd
import numpy as np
import re
import joblib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---------------------------------------------------------
# Helper Functions for Scoring (0.0 to 1.0)
# ---------------------------------------------------------

def check_constraint(job_desc, cv_text, regex_pattern):
    """Returns 1 if hard constraint is met or not required, 0 if missing."""
    job_requires = bool(re.search(regex_pattern, job_desc))
    if not job_requires: return 1
    return 1 if bool(re.search(regex_pattern, cv_text)) else 0

def calc_match_score(job_desc, cv_text, pattern):
    """Calculates a soft score (0.0 to 1.0) based on keyword overlap."""
    job_keywords = set(re.findall(pattern, job_desc))
    if not job_keywords: return 1.0 # Not required
    
    cv_keywords = set(re.findall(pattern, cv_text))
    matches = job_keywords.intersection(cv_keywords)
    return len(matches) / len(job_keywords)

def extract_svm_features(job_text, cv_text):
    """Extracts the exact 9 features needed for the SVM model."""
    constraints = {
        "Req_Experience": r"שנות ניסיון|ניסיון חובה|ניסיון של", 
        "Req_Driving": r"רישיון b|רישיון c|רישיון ג|משאית|מלגזה|צמ\"ה|טרקטור|רישיון e|רכב כבד",
        "Req_Security_License": r"רישיון נשק|נושא נשק|רובאי 07|רובאי 08|קורס אחיד|קורס מונחה",
        "Req_Gov_License": r"רואה חשבון|רו\"ח|עורך דין|עו\"ד|רישיון משרד הבריאות|אח מוסמך|חשמלאי מוסמך|מהנדס רשום",
        "Req_Student": r"משרת סטודנט|סטודנט/ית|סטודנט פעיל",
        "Req_Security_Clearance": r"סיווג ביטחוני|סיווג בטחוני",
        "Req_Finance_Cert": r"הנהלת חשבונות סוג|חשב שכר מוסמך|יועץ פנסיוני",
        "Req_Edu_Sport_Cert": r"תעודת הוראה|מדריך מוסמך|תעודת מדריך|עזרה ראשונה",
        "Req_Languages": r"אנגלית שפת אם|צרפתית שפת אם|ערבית שפת אם"
    }
    
    features = {}
    for name, pattern in constraints.items():
        features[name] = check_constraint(job_text, cv_text, pattern)
    
    # Return as a DataFrame with one row
    return pd.DataFrame([features])

# ---------------------------------------------------------
# Main Generation Function
# ---------------------------------------------------------

def generate_mlp_data():
    print("Loading models... (This might take a moment)")
    
    # 1. Load RoBERTa
    model_path = "./saved_matching_model"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    roberta_model = AutoModelForSequenceClassification.from_pretrained(model_path)
    roberta_model.eval() # Set to evaluation mode
    
    # 2. Load SVM
    svm_model = joblib.load("svm_model.pkl")
    
    # 3. Load Data and take a sample of 300 rows
    print("Loading dataset and sampling 300 rows...")
    df_full = pd.read_csv("ai_training_dataset.csv")
    df_sample = df_full.sample(n=300, random_state=42).reset_index(drop=True)
    
    mlp_dataset = []
    
    print("Starting feature extraction for 300 rows...")
    print("Please wait, RoBERTa is reading the texts...")

    for index, row in df_sample.iterrows():
        job_text = str(row.get('Job_Description', '')).lower()
        cv_text = str(row.get('CV_Text', '')).lower()
        actual_label = row.get('Label', 0)
        
        # --- Feature 1: RoBERTa Score ---
        inputs = tokenizer(job_text, cv_text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = roberta_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            roberta_score = probs[0][1].item() # Probability of Match (Class 1)
            
        # --- Feature 2: SVM Confidence ---
        svm_input = extract_svm_features(job_text, cv_text)
        svm_probs = svm_model.predict_proba(svm_input)
        svm_confidence = svm_probs[0][1] # Probability of passing hard constraints
        
        # --- Feature 3: Hard Skills ---
        hard_skills_pattern = r"python|sql|java|c\+\+|excel|b2b|agile|aws|linux|react|node|html|css"
        hard_skills_score = calc_match_score(job_text, cv_text, hard_skills_pattern)
        
        # --- Feature 4: Location Match (Simple heuristic) ---
        location_pattern = r"תל אביב|ירושלים|חיפה|באר שבע|ראשון לציון|פתח תקווה|אשדוד|נתניה"
        location_score = calc_match_score(job_text, cv_text, location_pattern)
        
        # --- Feature 5: Work Model Match ---
        work_model_pattern = r"מהבית|היברידי|משולב|משרד"
        work_model_score = calc_match_score(job_text, cv_text, work_model_pattern)
        
        # --- Feature 6: Education Score ---
        education_pattern = r"תואר ראשון|תואר שני|ba|bsc|ma|mba|מהנדס"
        education_score = calc_match_score(job_text, cv_text, education_pattern)
        
        # --- Feature 7: Languages Match ---
        lang_pattern = r"אנגלית|רוסית|ערבית|צרפתית|ספרדית"
        languages_score = calc_match_score(job_text, cv_text, lang_pattern)
        
        # --- Feature 8: Management Bonus ---
        mgmt_pattern = r"ניהול|ראש צוות|מנהל|הובלת|אחריות על עובדים|קצין"
        management_score = calc_match_score(job_text, cv_text, mgmt_pattern)
        
        # --- Feature 9: Military Bonus ---
        military_pattern = r"8200|ממר\"ם|תקשוב|מודיעין|קצין|לוחם|קרבי"
        military_score = calc_match_score(job_text, cv_text, military_pattern)
        
        # --- Feature 10: Soft Skills Match ---
        soft_skills_pattern = r"עבודת צוות|תחת לחץ|יחסי אנוש|ראש גדול|למידה עצמית|אוטודידקט"
        soft_skills_score = calc_match_score(job_text, cv_text, soft_skills_pattern)
        
        # Add to the new dataset (using 1.0 for features 11-13 as placeholders to keep it simple and fast)
        mlp_dataset.append({
            'RoBERTa_Score': round(roberta_score, 4),
            'SVM_Confidence': round(svm_confidence, 4),
            'Hard_Skills_Match': round(hard_skills_score, 4),
            'Location_Score': round(location_score, 4),
            'Work_Model_Score': round(work_model_score, 4),
            'Experience_Bonus': 1.0, # Placeholder for simplicity in this dataset
            'Education_Score': round(education_score, 4),
            'Languages_Match': round(languages_score, 4),
            'Management_Bonus': round(management_score, 4),
            'Military_Bonus': round(military_score, 4),
            'Availability_Score': 1.0, # Placeholder
            'Mobility_Score': 1.0, # Placeholder
            'Soft_Skills_Match': round(soft_skills_score, 4),
            'Actual_Label': actual_label # The true answer (1 or 0)
        })
        
        if (index + 1) % 50 == 0:
            print(f"Processed {index + 1} / 300 rows...")

    print("Finished processing all rows!")
    
    # Save the new dataset
    mlp_df = pd.DataFrame(mlp_dataset)
    output_file = "mlp_training_data.csv"
    mlp_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"Successfully saved MLP training data to: {output_file}")
    print("\nData Preview:")
    print(mlp_df.head())

if __name__ == "__main__":
    generate_mlp_data()