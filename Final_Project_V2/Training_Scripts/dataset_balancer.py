import pandas as pd
import random
import uuid

def assign_category(title, taxonomy):
    """
    Categorizes an existing job based on keywords in its title.
    """
    if not isinstance(title, str):
        return "כללי וללא ניסיון"
        
    title_lower = title.lower()
    for category, keywords in taxonomy.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                return category
                
    return "כללי וללא ניסיון"

def generate_synthetic_job(category, keywords):
    """
    Generates a synthetic job posting matching our exact schema.
    """
    company_prefixes = ["חברת", "קבוצת", "ארגון", "משרד", "תאגיד"]
    company_suffixes = ["בעמ", "פתרונות", "ישראל", "החזקות", "טכנולוגיות"]
    
    locations = ["תל אביב", "חיפה", "ירושלים", "באר שבע", "נתניה", "פתח תקווה", "מהבית", "היברידי"]
    job_types = ["משרה מלאה", "משרה חלקית", "משמרות", "פרילנס"]
    
    job_title = random.choice(keywords)
    company_name = f"{random.choice(company_prefixes)} {random.choice(keywords).split()[0]} {random.choice(company_suffixes)}"
    
    desc_templates = [
        f"דרוש/ה {job_title} להשתלבות בצוות דינמי. התפקיד כולל עבודה מאתגרת ודורש ניסיון בתחום ה{category}. תנאים מעולים למתאימים.",
        f"ל{company_name} דרוש/ה {job_title}. אנו מחפשים עובד/ת רציני/ת לפיתוח קריירה ארוכת טווח. ידע קודם בתחום חובה.",
        f"הזדמנות מעולה! דרוש/ה {job_title} לעבודה מידית. נדרשת הבנה מעמיקה ב{category}. סביבת עבודה נעימה ומתגמלת."
    ]
    
    full_desc = random.choice(desc_templates)
    
    return {
        "Job_ID": f"SYN_{uuid.uuid4().hex[:8].upper()}",
        "Company_Name": company_name,
        "Category": category,
        "Job_Title": job_title,
        "Full_Description": full_desc,
        "Salary": "",
        "Work_Model": random.choice(["מהבית", "היברידי", "משרד"]),
        "Job_Type": random.choice(job_types),
        "Location": random.choice(locations),
        "Availability": "מיידית",
        "Experience_Years": str(random.randint(0, 3)),
        "Education": "",
        "Languages": "",
        "Minimum_Age": "",
        "Tools": "",
        "Travel_Expenses": ""
    }

def process_and_balance_dataset(input_csv, output_csv, min_jobs_per_category=50):
    """
    Reads the raw dataset, categorizes it, and balances it by generating synthetic jobs.
    """
    print(f"Loading raw dataset from {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: Could not find '{input_csv}'. Please verify the file name.")
        return

    master_taxonomy = {
        "אבטחת מידע וסייבר": ["סייבר", "אבטחת מידע", "SOC", "נוזקות", "CISO"],
        "אדמיניסטרציה": ["מזכיר", "אדמיניסטרציה", "פקיד", "מנהל משרד", "בק אופיס", "מרכזן"],
        "אופנה וטקסטיל": ["אופנה", "קניין אופנה", "תופר", "תדמיתן", "מעצב אופנה"],
        "אינטרנט ודיגיטל": ["דיגיטל", "PPC", "SEO", "סושיאל", "כותב תוכן", "קמפיינר"],
        "ביטוח": ["ביטוח", "חתם", "פנסיוני", "תביעות", "סוכן ביטוח"],
        "בכירים / ניהול": ["מנכל", "סמנכל", "דירקטור", "מנהל אגף"],
        "בנייה ונדלן": ["בניין", "נדלן", "קבלן", "אדריכל", "מפקח בניה", "שמאי"],
        "בעלי מקצוע": ["חשמלאי", "טכנאי", "אינסטלטור", "אחזקה", "נגר", "רתך"],
        "הדרכה / הוראה": ["מורה", "מדריך", "גננת", "סייעת", "הוראה", "חינוך"],
        "הייטק-QA": ["QA", "בודק תוכנה", "בדיקות ידניות", "Automation", "בדיקות תוכנה"],
        "הייטק-חומרה": ["חומרה", "אלקטרוניקה", "ASIC", "VLSI", "FPGA", "Embedded"],
        "הייטק-כללי": ["מוצר", "פרויקטים", "מערכות מידע", "סיסטם", "IT", "DevOps"],
        "הייטק-תוכנה": ["תוכנה", "מפתח", "מתכנת", "Full Stack", "Backend", "Frontend", "Java", "Python"],
        "הנדסה": ["מהנדס מכונות", "מהנדס תעשייה", "הנדסאי", "מהנדס חשמל", "מהנדס חומרים"],
        "התנדבות": ["מתנדב", "התנדבות", "עמותה", "שנת שירות"],
        "יופי, טיפוח וספא": ["קוסמטיקאית", "ספר", "מאפר", "פדיקור", "קליניקה"],
        "כספים / שוק ההון": ["רואה חשבון", "חשב", "הנהלת חשבונות", "כלכלן", "בנק", "אשראי"],
        "לוגיסטיקה / שילוח": ["מחסנאי", "מלקט", "שילוח", "לוגיסטיקה", "שרשרת אספקה"],
        "מדעים / ביוטק": ["מעבדה", "כימאי", "ביולוג", "ביוטק", "מחקר קליני"],
        "מכירות": ["מכירות", "סוכן שטח", "טלמרקטינג", "קמעונאות", "ניהול לקוחות"],
        "מלונאות / מסעדנות": ["מלצר", "ברמן", "טבח", "מסעדה", "מלון", "קונדיטור"],
        "משאבי אנוש": ["משאבי אנוש", "גיוס", "HR", "מראיין", "רווחה"],
        "עבודה מהבית": ["מהבית", "סקרים", "קצין מבחן", "עבודה מרחוק"],
        "עיצוב": ["עיצוב", "גרפי", "אנימטור", "פנים", "תלת מימד"],
        "עריכת דין": ["עורך דין", "משפט", "מתמחה", "חוזים", "ליטיגציה"],
        "פרסום / מדיה / תקשורת": ["פרסום", "מדיה", "תקשורת", "עיתונאי", "תקציבאי", "וידאו"],
        "קמעונאות": ["קופאי", "סדרן", "סופרמרקט", "קמעונאות"],
        "רכב / תחבורה": ["רכב", "נהג", "מכונאי", "תחבורה", "פחח"],
        "רפואה / בריאות": ["אח", "אחות", "רופא", "רפואה", "סיעוד", "רוקח"],
        "שיווק": ["שיווק", "מותג", "אסטרטגיה", "מרקום"],
        "שירות לקוחות": ["שירות", "מוקד", "נציג", "תמיכה", "אחמש"],
        "שמירה / אבטחה": ["אבטחה", "שומר", "קבוט", "סייר", "ביטחון"],
        "תיירות/ תעופה": ["תיירות", "תעופה", "סוכן נסיעות", "דייל", "טייס"],
        "תעשיה / ייצור": ["ייצור", "תעשייה", "מפעיל מכונה", "עובד ייצור", "cnc"]
    }

    print("Categorizing existing jobs...")
    df['Category'] = df['Job_Title'].apply(lambda x: assign_category(x, master_taxonomy))
    
    current_counts = df['Category'].value_counts().to_dict()
    
    synthetic_jobs_added = 0
    new_jobs_list = []

    print(f"Checking balance. Target is {min_jobs_per_category} jobs per category.")
    
    for category, keywords in master_taxonomy.items():
        count = current_counts.get(category, 0)
        
        if count < min_jobs_per_category:
            deficit = min_jobs_per_category - count
            print(f"[{category}] has {count} jobs. Generating {deficit} synthetic jobs...")
            
            for _ in range(deficit):
                syn_job = generate_synthetic_job(category, keywords)
                new_jobs_list.append(syn_job)
                synthetic_jobs_added += 1

    if synthetic_jobs_added > 0:
        df_synthetic = pd.DataFrame(new_jobs_list)
        df_balanced = pd.concat([df, df_synthetic], ignore_index=True)
        df_balanced.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print("---------------------------------------------------")
        print(f"Successfully generated {synthetic_jobs_added} synthetic jobs.")
        print(f"Balanced dataset saved to: {output_csv}")
        print("---------------------------------------------------")
    else:
        print("Dataset is already well balanced!")
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    # PLEASE VERIFY THIS MATCHES YOUR ALLJOBS CSV FILENAME
    INPUT_FILE = "alljobs_massive_dataset.csv" 
    OUTPUT_FILE = "balanced_massive_dataset.csv"
    
    process_and_balance_dataset(INPUT_FILE, OUTPUT_FILE, min_jobs_per_category=50)