import pandas as pd
import re

def check_constraint(job_desc, cv_text, regex_pattern):
    """
    Checks if a job requires a specific constraint.
    If it does, it checks if the CV meets this constraint.
    Returns 1 if the constraint is met OR not required.
    Returns 0 if the constraint is required but missing from the CV.
    """
    job_requires = bool(re.search(regex_pattern, job_desc))
    
    if not job_requires:
        return 1
        
    cv_has_it = bool(re.search(regex_pattern, cv_text))
    
    if cv_has_it:
        return 1
    else:
        return 0

def extract_svm_features(input_csv, output_csv):
    """
    Reads the main dataset, extracts all 9 binary features using regex,
    and saves a new dataset ready for SVM training.
    """
    print(f"Loading data from {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print("Error: Input file not found.")
        return

    # 9 Explicit Hard Constraints Mapping
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

    print("Extracting 9 features for SVM... This might take a few seconds.")
    
    svm_data = []

    for index, row in df.iterrows():
        job_text = str(row.get('Job_Description', '')).lower()
        cv_text = str(row.get('CV_Text', '')).lower()
        label = row.get('Label', 0)
        
        feature_row = {}
        
        for constraint_name, pattern in constraints.items():
            feature_row[constraint_name] = check_constraint(job_text, cv_text, pattern)
            
        feature_row['Label'] = label
        svm_data.append(feature_row)

    svm_df = pd.DataFrame(svm_data)
    svm_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"Successfully processed {len(svm_df)} rows.")
    print(f"Feature dataset saved to: {output_csv}")
    print("\nData Preview:")
    print(svm_df.head())

if __name__ == "__main__":
    INPUT_FILE = "ai_training_dataset.csv"
    OUTPUT_FILE = "svm_training_data.csv"
    
    extract_svm_features(INPUT_FILE, OUTPUT_FILE)