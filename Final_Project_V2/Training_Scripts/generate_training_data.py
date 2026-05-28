import pandas as pd
import random

# Simple translation/template helpers to generate clean context-aware CVs automatically
CV_TEMPLATES = {
    "אבטחת מידע וסייבר": [
        "Cybersecurity student with hands-on experience in SOC operations, penetration testing, Linux, and network security protocols.",
        "Information Security specialist focused on log analysis, firewall management, and vulnerability assessment tools."
    ],
    "מלונאות / מסעדנות": [
        "Experienced event waiter with excellent customer service skills, energetic personality, and passion for dynamic restaurant teamwork.",
        "Professional bartender and waiter with extensive hospitality background, looking for evening or weekend shifts."
    ],
    "הייטק-תוכנה": [
        "Full Stack Developer proficient in Python, Java, and modern backend architectures. Experienced in building robust APIs.",
        "Software Engineer with a focus on web development, clean code practices, and database optimization."
    ],
    "שמירה / אבטחה": [
        "Responsible security officer with background in physical protection, crowd control, and emergency response procedures.",
        "Dedicated security guard holding all necessary permits, looking for shifts or steady operations."
    ]
}

def build_scientific_dataset():
    input_path = "Data/balanced_massive_dataset.csv"
    output_path = "Data/ai_training_dataset.csv"
    
    print(f"Reading balanced jobs from {input_path}...")
    try:
        jobs_df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: Could not find {input_path}")
        return

    # Filter out categories we don't have predefined CV templates for to guarantee precise semantic training
    supported_categories = list(CV_TEMPLATES.keys())
    filtered_jobs = jobs_df[jobs_df['Category'].isin(supported_categories)].copy()
    
    if len(filtered_jobs) == 0:
        print("Warning: No matching categories found. Using default generic mapping.")
        return

    records = []
    job_list = filtered_jobs.to_dict('records')
    
    print("Generating positive and negative semantic pairs...")
    
    for job in job_list:
        category = job['Category']
        job_desc = job['Full_Description']
        job_title = job['Job_Title']
        
        # 1. Create POSITIVE pair (Label = 1) -> Same category matching text
        pos_cv = random.choice(CV_TEMPLATES[category])
        records.append({
            "Job_Title": job_title,
            "Job_Description": job_desc,
            "CV_Text": pos_cv,
            "Label": 1
        })
        
        # 2. Create NEGATIVE pair (Label = 0) -> Completely different category text
        wrong_categories = [c for c in supported_categories if c != category]
        wrong_cat = random.choice(wrong_categories)
        neg_cv = random.choice(CV_TEMPLATES[wrong_cat])
        records.append({
            "Job_Title": job_title,
            "Job_Description": job_desc,
            "CV_Text": neg_cv,
            "Label": 0
        })

    # Save to final training dataset file
    final_df = pd.DataFrame(records)
    # Shuffle the dataset so the trainer doesn't get 1s and 0s sequentially
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Successfully constructed {len(final_df)} clean training pairs at {output_path}!")

if __name__ == "__main__":
    build_scientific_dataset()