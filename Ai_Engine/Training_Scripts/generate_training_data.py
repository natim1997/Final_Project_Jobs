import pandas as pd
import random

# רשימת הקטגוריות המלאה שלך
CATEGORIES = [
    "חינוך והוראה", "בעלי חיים", "הפקה ואירועים", "רפואה ורווחה", "טכנולוגיה",
    "בניין וייצור", "משלוחים ותחבורה", "מסעדנות", "אבטחה וביטחון",
    "אפסנאות ולוגיסטיקה", "שירות לקוחות", "עיצוב וקריאייטיב", "מכירות ואופנה", "אחזקה"
]

def generate_candidate_text():
    # יצירת טקסט עשיר המבוסס על שדות המועמד
    skills = ["Java", "Python", "SAP", "Excel", "English", "Driving License"]
    return f"Candidate Details: Name: {random.randint(1000, 9999)}, Address: Tel Aviv, " \
           f"Search Radius: {random.randint(5, 30)}km, Skills: {', '.join(random.sample(skills, 2))}, " \
           f"Soft Skills: Team player, Fast learner."

def generate_job_text(category):
    # יצירת טקסט עשיר המבוסס על שדות המשרה
    return f"Job Category: {category}, Company: TechCorp, Salary: {random.randint(30, 80)} per hour, " \
           f"Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in shifts. " \
           f"Location: Tel Aviv, Contact: 050-1234567."

def build_scientific_dataset():
    output_path = "Data/ai_training_dataset.csv"
    records = []
    
    print("Generating enriched training pairs...")
    
    for _ in range(5000):
        cat = random.choice(CATEGORIES)
        
        records.append({
            "Job_Description": generate_job_text(cat),
            "CV_Text": generate_candidate_text() + f" Looking for {cat} job.",
            "Label": 1
        })
        
        wrong_cat = random.choice([c for c in CATEGORIES if c != cat])
        records.append({
            "Job_Description": generate_job_text(cat),
            "CV_Text": generate_candidate_text() + f" Looking for {wrong_cat} job.",
            "Label": 0
        })

    final_df = pd.DataFrame(records).sample(frac=1, random_state=42)
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Dataset ready with {len(final_df)} enriched samples!")

if __name__ == "__main__":
    build_scientific_dataset()