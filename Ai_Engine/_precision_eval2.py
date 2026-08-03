# Precision@5 test on real casual/entry-level jobs (ClickJob's real target
# users). Ground truth was decided by reading job text before running the model.
import sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
from final_pipeline import JobMatcherPipeline

pipeline = JobMatcherPipeline()

df = pd.read_csv('Data/alljobs_massive_dataset.csv', encoding='utf-8')
df = df.dropna(subset=['Job_Title', 'Full_Description'])
casual_markers = ['ללא ניסיון', 'אין צורך בניסיון', 'סטודנטים', 'סטודנטיות', 'גמישות מלאה', 'שכר שעתי', 'שעתי', 'משמרות']
mask = df['Full_Description'].str.contains('|'.join(casual_markers), na=False) | df['Job_Title'].str.contains('|'.join(casual_markers), na=False)
casual = df[mask]
sample = casual.sample(n=70, random_state=7).reset_index(drop=True)

jobs = []
for i, row in sample.iterrows():
    jobs.append({"idx": i, "title": str(row["Job_Title"]), "description": str(row["Full_Description"])[:800], "category": ""})

candidates = [
    {
        "id": "security_guard",
        "bio": "מאבטח/ת עם קורס בסיסי א' בתוקף, ניסיון באבטחת מוסדות ואתרים, זמינות למשמרות כולל סופי שבוע. אחראי/ת ורציני/ת.",
        "relevant": {0, 3, 13, 17, 55, 59},
    },
    {
        "id": "customer_service_sales",
        "bio": "נציג/ת שירות ומכירה עם ניסיון במתן מענה פרונטלי וטלפוני ללקוחות, יכולת מכירתית ושירותיות גבוהה, זמין/ה למשמרות מגוונות.",
        "relevant": {1, 7, 24, 27, 33, 37},
    },
    {
        "id": "waiter",
        "bio": "מלצר/ית עם ניסיון במסעדות ובבתי מלון, תודעת שירות גבוהה, זמין/ה למשמרות כולל סופי שבוע וחגים.",
        "relevant": {43, 56, 12},
    },
    {
        "id": "retail_cashier",
        "bio": "קופאי/ת וסדרן/ית עם ניסיון בעבודה ברשת קמעונאית, זמינות למשמרות בוקר וערב, אחראי/ת ומהיר/ה בלמידה.",
        "relevant": {20, 50, 57},
    },
    {
        "id": "warehouse_production",
        "bio": "עובד/ת ייצור ומחסן עם ניסיון בעבודה פיזית, אריזה ותפעול קווי ייצור, זמין/ה למשמרות ועבודה בצוות.",
        "relevant": {25, 51, 54, 67},
    },
    {
        "id": "admin_reception",
        "bio": "מזכיר/ה ופקיד/ת קבלה עם ניסיון בעבודה אדמיניסטרטיבית, מענה טלפוני, קביעת תורים ושירות לקוחות במשרד.",
        "relevant": {4, 26, 6},
    },
    {
        "id": "tech_support",
        "bio": "נציג/ת תמיכה טכנית עם ניסיון בפתרון תקלות מחשוב ותקשורת, עבודה מול לקוחות והיכרות עם מערכות טכניות.",
        "relevant": {2, 40, 58, 68},
    },
    {
        "id": "driver",
        "bio": "נהג/ת חלוקה עם רישיון נהיגה בתוקף מעל 12 טון, ניסיון בהפצה ובשירות לקוחות בשטח, אחראי/ת ומדויק/ת בזמנים.",
        "relevant": {65, 16},
    },
    {
        "id": "financial_phone_rep",
        "bio": "נציג/ת שירות פיננסי/ביטוחי עם ניסיון במענה טלפוני ללקוחות בתחום הבנקאות, ההלוואות או הביטוח, שירותיות גבוהה ואוריינטציה ללקוח.",
        "relevant": {18, 31, 52, 60, 61, 46},
    },
    {
        "id": "student_flexible",
        "bio": "סטודנט/ית מחפש/ת עבודה מזדמנת וגמישה, ללא ניסיון קודם ספציפי, פנוי/ה למשמרות בוקר וערב, אחראי/ת ולומד/ת מהר.",
        "relevant": {57, 20, 33, 1},
    },
]

results = []
for cand in candidates:
    payload = {"id": cand["id"], "semantic_profile": cand["bio"], "distance_to_job": 1, "searchRadius": 999, "jobCatagories": [], "softSkills": []}
    scored = []
    for job in jobs:
        job_json = {"category": job["category"], "title": job["title"], "description": job["description"]}
        r = pipeline.evaluate_candidate(job_json, payload)
        scored.append((job["idx"], r["Final_Score"], job["title"]))
    scored.sort(key=lambda x: x[1], reverse=True)
    top5 = scored[:5]
    hits = sum(1 for idx, score, title in top5 if idx in cand["relevant"])
    precision = hits / 5.0
    results.append((cand["id"], precision, top5, cand["relevant"]))

with open("precision_results_2.txt", "w", encoding="utf-8") as f:
    total_p = 0
    for cid, precision, top5, relevant in results:
        f.write(f"=== {cid} (ground-truth relevant: {sorted(relevant)}) ===\n")
        f.write(f"Precision@5 = {precision:.2f}\n")
        for idx, score, title in top5:
            mark = "RELEVANT" if idx in relevant else "not relevant"
            f.write(f"  [{idx:2d}] score={score:3d}  ({mark})  {title[:70]}\n")
        f.write("\n")
        total_p += precision
    f.write(f"\n=== OVERALL MEAN Precision@5 across {len(results)} candidates: {total_p/len(results):.3f} ===\n")

print("DONE")
