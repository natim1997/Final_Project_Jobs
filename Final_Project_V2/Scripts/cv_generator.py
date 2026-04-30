import pandas as pd
import random
import re

def clean_text(text):
    """
    Cleans the raw text by removing extra spaces, newlines, and weird characters.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_synthetic_cv(job_desc, job_title, match_type):
    """
    Generates a synthetic CV text based on the job description.
    match_type = 1: Creates a matching CV
    match_type = 0: Creates a non-matching CV
    This version randomly selects between Hebrew, English, and Mixed language templates
    to train the XLM-RoBERTa model on real-world Israeli phrasing (code-switching).
    """
    
    # 1. Hebrew Templates
    templates_he = [
        "סטודנט עם מוטיבציה גבוהה וניסיון ב{skills}. מחפש משרה בתור {title}. פנוי לעבודה במשמרות.",
        "איש מקצוע יסודי עם רקע ב{skills}. לומד מהר ואיש צוות מעולה. אשמח להשתלב בתפקיד {title}.",
        "מחפש עבודה בתחום ה{title}. יש לי ניסיון רלוונטי ב{skills} ואני זמין לעבודה מידית."
    ]
    
    # 2. English Templates
    templates_en = [
        "Highly motivated student with experience in {skills}. Looking for a position as {title}. Available for flexible shifts.",
        "Experienced professional in {skills}. Quick learner, excellent team player. Seeking a role in {title}.",
        "I am a fast learner with a strong background in {skills}. I am very interested in the {title} position and can start immediately."
    ]
    
    # 3. Mixed (Hebrew & English) Templates
    templates_mixed = [
        "סטודנט עם ניסיון ב- {skills}. Looking for a full time or part time job as {title}. פנוי למשמרות גמישות.",
        "Highly motivated professional. יש לי ניסיון רב ב{skills}. אשמח להשתלב בחברה בתפקיד {title}.",
        "Background in {skills}. מחפש משרה מאתגרת ודינמית בתור {title}. Available immediately."
    ]
    
    # Unrelated skills to generate negative matches (Label 0)
    unrelated_skills_he = [
        "הפעלת ציוד כבד וטרקטורים",
        "ראיית חשבון ודיני מיסים",
        "מחקר במעבדת ביולוגיה מולקולרית",
        "כתיבת תוכן שיווקי למשרדי נדלן",
        "בישול ואפייה במסעדות שף"
    ]
    
    unrelated_skills_en = [
        "Python programming and Machine Learning",
        "Heavy machinery and crane operation",
        "Advanced accounting and corporate tax law",
        "Medical surgery and biology research",
        "Quantum physics and theoretical math"
    ]
    
    unrelated_skills_mixed = [
        "פיתוח ב- Python and Data Science",
        "ניהול קמפיינים ב- Social Media",
        "Customer Success management ושירות פרונטלי",
        "Sales and marketing בעולם הנדלן",
        "Financial analysis וראיית חשבון מורכבת"
    ]

    # Randomly choose the language style for this specific CV
    lang_choice = random.choice(['he', 'en', 'mixed'])
    
    if lang_choice == 'he':
        selected_template = random.choice(templates_he)
        unrelated_pool = unrelated_skills_he
        unrelated_title = "תחום שונה לחלוטין"
        matched_skills_text = f"תחומים הקשורים ל-{job_title}"
        
    elif lang_choice == 'en':
        selected_template = random.choice(templates_en)
        unrelated_pool = unrelated_skills_en
        unrelated_title = "a completely different field"
        matched_skills_text = f"areas related to {job_title}"
        
    else:
        selected_template = random.choice(templates_mixed)
        unrelated_pool = unrelated_skills_mixed
        unrelated_title = "תחום אחר לגמרי / completely different role"
        matched_skills_text = f"תחומים רלוונטיים for {job_title}"
        
    # Inject the variables into the chosen template
    if match_type == 1:
        # Match: We use the actual job title and pretend the user has the relevant skills
        cv_text = selected_template.format(skills=matched_skills_text, title=job_title)
    else:
        # No Match: We use a totally unrelated job title and skills
        random_skill = random.choice(unrelated_pool)
        cv_text = selected_template.format(skills=random_skill, title=unrelated_title)
        
    return cv_text

def build_training_dataset(input_csv, output_csv, sample_size=5000):
    """
    Reads the scraped jobs, cleans them, generates synthetic CVs, 
    and creates the final labeled dataset for the XLM-RoBERTa model.
    """
    print(f"Loading data from {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print("Error: Could not find the input CSV file. Please check the name.")
        return

    # Drop rows without a description or title
    df = df.dropna(subset=['Full_Description', 'Job_Title'])
    
    # If the dataset is huge, we sample a portion to balance processing time and data quality
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        
    training_data = []
    
    print("Generating synthetic CVs and labels in multiple languages...")
    
    for index, row in df.iterrows():
        job_desc = clean_text(row['Full_Description'])
        job_title = clean_text(row['Job_Title'])
        
        # Skip jobs with descriptions that are too short to be meaningful
        if len(job_desc) < 20:
            continue
            
        # Create one positive example (Label 1)
        positive_cv = generate_synthetic_cv(job_desc, job_title, match_type=1)
        training_data.append({
            "Job_Title": job_title,
            "Job_Description": job_desc,
            "CV_Text": positive_cv,
            "Label": 1
        })
        
        # Create one negative example (Label 0)
        negative_cv = generate_synthetic_cv(job_desc, job_title, match_type=0)
        training_data.append({
            "Job_Title": job_title,
            "Job_Description": job_desc,
            "CV_Text": negative_cv,
            "Label": 0
        })

    # Convert the new list of dictionaries to a Pandas DataFrame
    training_df = pd.DataFrame(training_data)
    
    # Shuffle the dataset thoroughly so 1s and 0s are randomly mixed
    training_df = training_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to a new CSV, ready for AI training
    training_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"Success. Multilingual training dataset created with {len(training_df)} rows.")
    print(f"Saved to: {output_csv}")

if __name__ == "__main__":
    # Point this to the balanced file we just created
    INPUT_FILE = "balanced_massive_dataset.csv" 
    OUTPUT_FILE = "ai_training_dataset.csv"
    
    # We will generate 10,000 pairs (5000 matches, 5000 non-matches) for the dataset
    build_training_dataset(INPUT_FILE, OUTPUT_FILE, sample_size=5000)