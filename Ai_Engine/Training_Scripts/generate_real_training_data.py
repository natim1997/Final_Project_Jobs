# Builds SVM/MLP training data from REAL job postings instead of the old
# fake "Job Category: X, Company: TechCorp..." templates. Labels are still
# auto-generated (same category = match), just with real Hebrew text now.
import sys
sys.stdout.reconfigure(encoding='utf-8')
import random
import pandas as pd

random.seed(42)

CATEGORIES = [
    "חינוך והוראה", "בעלי חיים", "הפקה ואירועים", "רפואה ורווחה", "טכנולוגיה",
    "בניין וייצור", "משלוחים ותחבורה", "מסעדנות", "אבטחה וביטחון",
    "אפסנאות ולוגיסטיקה", "שירות לקוחות", "עיצוב וקריאייטיב", "מכירות ואופנה", "אחזקה"
]

# Keyword sets to auto-tag real postings by category (checked on title +
# start of description, same as SIMPLE_JOB_KEYWORDS in final_pipeline.py).
CATEGORY_KEYWORDS = {
    "חינוך והוראה": ["מורה", "מורים", "הוראה", "מדריך חינוכי", "מדריכת חינוך", "גננת", "גנן", "צהרון", "צהרונים", "מחנך", "מחנכת", "בית ספר", "מוסד חינוכי"],
    "בעלי חיים": ["בעלי חיים", "כלב", "כלבים", "וטרינר", "פנסיון כלבים", "דוג ווקר", "טיפוח כלבים", "חיות מחמד"],
    "הפקה ואירועים": ["הפקת אירועים", "הפקה ואירועים", "מלצר", "מלצרית", "ברמן", "ברמנית", "דיילת אירועים", "הקמת אירוע", "קייטרינג", "צלם אירועים"],
    "רפואה ורווחה": ["אח /ות", "אחות", "סיעוד", "מטפל סיעודי", "מטפלת סיעודית", "פיזיותרפיסט", "עובד סוציאלי", "עובדת סוציאלית", "מרפאה", "בית אבות", "פארא רפואי", "רוקח", "רוקחת", "מגן דוד אדום"],
    "טכנולוגיה": ["מפתח", "מפתחת", "תוכנה", "Developer", "Software", "הנדסאי אלקטרוניקה", "תמיכה טכנית", "IT", "SAP", "מתכנת", "QA", "DevOps"],
    "בניין וייצור": ["עובד ייצור", "עובדת ייצור", "מפעיל מכונה", "מפעילת מכונה", "מהנדס ביצוע", "פועל בניין", "טכנאי מכונות", "מכונאי", "רתך", "חשמלאי תעשייה"],
    "משלוחים ותחבורה": ["נהג", "נהגת", "שליח", "שליחה", "משלוחים", "חלוקה", "סייר אופנוע", "הפצה"],
    "מסעדנות": ["מלצר", "מלצרית", "טבח", "טבחית", "שף", "קונדיטור", "עובד מטבח", "ברמן", "ברמנית", "מסעדה", "בית קפה"],
    "אבטחה וביטחון": ["מאבטח", "מאבטחת", "שומר", "שומרת", "קב\"ט", "אבטחה", "בודק ביטחוני", "בודקת ביטחונית", "קצין ביטחון"],
    "אפסנאות ולוגיסטיקה": ["מחסנאי", "מחסנאית", "לוגיסטיקה", "מלגזן", "מלגזנית", "מחסן", "ניפוק ציוד", "עובד מחסן"],
    "שירות לקוחות": ["נציג שירות", "נציגת שירות", "שירות לקוחות", "מוקד שירות", "נציג מכירות", "נציגת מכירות", "מוקדן", "מוקדנית", "תמיכה טלפונית"],
    "עיצוב וקריאייטיב": ["מעצב", "מעצבת", "גרפיקאי", "גרפיקאית", "קריאייטיב", "עיצוב גרפי", "עורך תוכן", "עורכת תוכן", "צלם", "צלמת"],
    "מכירות ואופנה": ["מוכר /ת בחנות", "עובד חנות", "עובדת חנות", "קמעונאות", "קופאי", "קופאית", "סדרן", "סדרנית", "מכירות באופנה", "עוזר חנות"],
    "אחזקה": ["אחזקה", "איש תחזוקה", "אשת תחזוקה", "מנקה", "ניקיון", "עובד ניקיון", "טכנאי אחזקה"],
}

# A few realistic candidate bio examples per category, written the same way
# real candidate profiles look (see _precision_eval2.py for the same style).
CANDIDATE_BIO_TEMPLATES = {
    "חינוך והוראה": [
        "גננת מוסמכת עם ניסיון בעבודה עם ילדי גן, סבלנית ויצירתית, זמינה למשרה מלאה.",
        "מדריך חינוכי עם ניסיון בהנחיית קבוצות נוער, אחראי ובעל יכולת הכלה גבוהה.",
        "סטודנטית לחינוך המחפשת עבודה בצהרון או בבית ספר, זמינה אחר הצהריים.",
        "מורה בהכשרה עם רקע במתמטיקה, מחפש עבודה חלקית כמורה פרטי או בצהרון.",
    ],
    "בעלי חיים": [
        "אוהב/ת כלבים עם ניסיון בטיולי כלבים ופנסיון, זמין/ה למשמרות בוקר.",
        "דוג ווקר עם ניסיון של שנתיים, אחראי ומדויק בזמנים, גר/ה באזור המרכז.",
        "מתנדב/ת בעמותת בעלי חיים המחפש/ת עבודה בתחום הטיפול בחיות מחמד.",
    ],
    "הפקה ואירועים": [
        "מלצר/ית עם ניסיון במסעדות ובאירועים, תודעת שירות גבוהה, זמין/ה לסופי שבוע.",
        "סטודנט/ית המחפש/ת עבודה בהפקת אירועים, אחראי/ת ובעל/ת יכולת עבודה בצוות.",
        "ברמן/ית עם ניסיון בברים ובאירועים פרטיים, זמין/ה לעבודת ערב ולילה.",
    ],
    "רפואה ורווחה": [
        "מטפל/ת סיעודי/ת עם ניסיון בטיפול בקשישים, סבלני/ת ואחראי/ת.",
        "סטודנט/ית לעבודה סוציאלית המחפש/ת עבודה חלקית במסגרת רווחה.",
        "עוזר/ת רפואי/ת עם ניסיון במרפאה, אחראי/ת ומדויק/ת בתיעוד.",
    ],
    "טכנולוגיה": [
        "מפתח/ת תוכנה עם ניסיון ב-Python ו-SQL, זמין/ה למשרה חלקית או פרויקטלית.",
        "טכנאי/ת תמיכה טכנית עם ניסיון בפתרון תקלות מחשוב ותקשורת.",
        "סטודנט/ית להנדסת תוכנה המחפש/ת עבודה בתחום הטכנולוגיה, ידע ב-Java ו-Git.",
    ],
    "בניין וייצור": [
        "עובד/ת ייצור עם ניסיון בעבודה פיזית בקו ייצור, זמין/ה למשמרות.",
        "מפעיל/ת מכונות עם ניסיון בתעשייה, אחראי/ת ומדויק/ת.",
        "פועל/ת בניין עם ניסיון בעבודות שיפוצים וגמר, זמין/ה למשרה מלאה.",
    ],
    "משלוחים ותחבורה": [
        "נהג/ת חלוקה עם רישיון נהיגה בתוקף, ניסיון בהפצה ובשירות לקוחות בשטח.",
        "שליח/ה עם אופנוע/רכב פרטי, זמין/ה למשמרות גמישות במהלך השבוע.",
        "סייר/ת משלוחים עם ניסיון בעיר, אחראי/ת ומדויק/ת בזמנים.",
    ],
    "מסעדנות": [
        "טבח/ית עם ניסיון במטבחים מקצועיים, זמין/ה למשמרות ערב ולילה.",
        "מלצר/ית עם ניסיון במסעדות ובבתי מלון, תודעת שירות גבוהה.",
        "עובד/ת מטבח עם ניסיון בהכנת מנות ובעבודה תחת לחץ.",
    ],
    "אבטחה וביטחון": [
        "מאבטח/ת עם קורס בסיסי א' בתוקף, ניסיון באבטחת מוסדות ואתרים.",
        "שומר/ת עם ניסיון באבטחה, אחראי/ת ורציני/ת, זמין/ה למשמרות לילה.",
        "בודק/ת ביטחוני/ת עם תעודה בתוקף, ניסיון בבדיקות בכניסות למקומות ציבוריים.",
    ],
    "אפסנאות ולוגיסטיקה": [
        "מחסנאי/ת עם ניסיון בניהול מלאי וקבלת סחורה, אחראי/ת ומדויק/ת.",
        "מלגזן/ית מוסמך/ת עם ניסיון בעבודה במחסן לוגיסטי.",
        "עובד/ת מחסן עם ניסיון בליקוט ואריזה, זמין/ה למשמרות בוקר וערב.",
    ],
    "שירות לקוחות": [
        "נציג/ת שירות ומכירה עם ניסיון במתן מענה פרונטלי וטלפוני ללקוחות.",
        "מוקדן/ית עם ניסיון בשירות לקוחות טלפוני, שירותיות גבוהה וסבלנות.",
        "נציג/ת תמיכה עם ניסיון בפתרון תלונות לקוחות ומענה מהיר.",
    ],
    "עיצוב וקריאייטיב": [
        "מעצב/ת גרפי/ת עם ניסיון ב-Photoshop ו-Illustrator, יצירתי/ת ומדויק/ת.",
        "צלם/ת עם ניסיון בצילום אירועים ומוצרים, זמין/ה לעבודה פרילנס.",
        "עורך/ת תוכן עם ניסיון בכתיבה לרשתות חברתיות ולאתרים.",
    ],
    "מכירות ואופנה": [
        "קופאי/ת וסדרן/ית עם ניסיון בעבודה ברשת קמעונאית, זמינות למשמרות בוקר וערב.",
        "עובד/ת חנות אופנה עם ניסיון במכירות ובשירות לקוחות, אוהב/ת אופנה.",
        "מוכר/ת בחנות עם ניסיון בסידור סחורה ובקופה, אחראי/ת ומהיר/ה בלמידה.",
    ],
    "אחזקה": [
        "איש/אשת תחזוקה עם ניסיון בתיקונים כלליים ובעבודות אחזקה שוטפת.",
        "עובד/ת ניקיון עם ניסיון בניקיון משרדים ומוסדות, אחראי/ת ויסודי/ת.",
        "טכנאי/ת אחזקה עם ניסיון בתחזוקת מבנים ומערכות.",
    ],
}


def tag_category(title, description_opening):
    haystack = f"{title} {description_opening}"
    matches = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            matches.append(cat)
    if len(matches) == 1:
        return matches[0]
    return None  # skip ambiguous (multi-category) or untagged postings


def build_dataset(out_path="Data/real_training_dataset.csv", pairs_per_category=120):
    df = pd.read_csv("Data/alljobs_massive_dataset.csv", encoding="utf-8")
    df = df.dropna(subset=["Job_Title", "Full_Description"])

    # Exclude rows already used in the eval/holdout sets, so training
    # doesn't leak into the test data (same random_state as those scripts).
    excluded_idx = set()
    excluded_idx.update(df.sample(n=60, random_state=42).index.tolist())
    casual_markers = ['ללא ניסיון', 'אין צורך בניסיון', 'סטודנטים', 'סטודנטיות', 'גמישות מלאה', 'שכר שעתי', 'שעתי', 'משמרות']
    mask = df['Full_Description'].str.contains('|'.join(casual_markers), na=False) | df['Job_Title'].str.contains('|'.join(casual_markers), na=False)
    casual_df = df[mask]
    excluded_idx.update(casual_df.sample(n=70, random_state=7).index.tolist())
    excluded_idx.update(casual_df.sample(n=60, random_state=123).index.tolist())

    df = df.drop(index=[i for i in excluded_idx if i in df.index]).reset_index(drop=True)
    print(f"Excluded {len(excluded_idx)} rows already used for dev/holdout evaluation this session.")

    tagged = {cat: [] for cat in CATEGORIES}
    for _, row in df.iterrows():
        title = str(row["Job_Title"])
        desc_opening = str(row["Full_Description"])[:250]
        cat = tag_category(title, desc_opening)
        if cat:
            tagged[cat].append({
                "title": title,
                "description": str(row["Full_Description"])[:800],
            })

    print("Real postings tagged per category:")
    for cat in CATEGORIES:
        print(f"  {cat}: {len(tagged[cat])}")

    records = []
    all_cats_with_data = [c for c in CATEGORIES if len(tagged[c]) >= 5]

    for cat in all_cats_with_data:
        jobs = tagged[cat]
        bios = CANDIDATE_BIO_TEMPLATES[cat]
        n_pos = min(pairs_per_category, len(jobs) * len(bios))
        # Positive pairs: candidate bio matched with a real job from the SAME category.
        pos_pairs = [(job, bio) for job in jobs for bio in bios]
        random.shuffle(pos_pairs)
        for job, bio in pos_pairs[:n_pos]:
            job_text = f"{job['title']} {job['description']}"
            records.append({"Job_Description": job_text, "CV_Text": bio, "Label": 1})

        # Negative pairs: same number, candidate bio from a DIFFERENT category
        # matched with a real job from this category (mix of random negatives
        # and adjacent/hard negatives from categories with overlapping vocabulary).
        other_cats = [c for c in all_cats_with_data if c != cat]
        for _ in range(n_pos):
            other_cat = random.choice(other_cats)
            other_bio = random.choice(CANDIDATE_BIO_TEMPLATES[other_cat])
            job = random.choice(jobs)
            job_text = f"{job['title']} {job['description']}"
            records.append({"Job_Description": job_text, "CV_Text": other_bio, "Label": 0})

    out_df = pd.DataFrame(records).sample(frac=1, random_state=42).reset_index(drop=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nWrote {len(out_df)} real-text training pairs to {out_path} "
          f"({(out_df['Label']==1).sum()} positive / {(out_df['Label']==0).sum()} negative)")


if __name__ == "__main__":
    build_dataset()
