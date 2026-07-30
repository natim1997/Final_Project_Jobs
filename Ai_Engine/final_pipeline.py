import re
import pandas as pd
import numpy as np
import joblib
import traceback
from sentence_transformers import SentenceTransformer, util

# ==========================================
# Helper Functions for JSON Data
# ==========================================

# Safely convert values to float
def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

# Safely convert values to int
def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

# Ensure value is always a list
def safe_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, str):
        return [val]
    return []

# ==========================================
# MODEL 1 — GATEKEEPER: reference data
# ==========================================

# Phrases that suggest the profile belongs to an employer posting work,
# not a candidate looking for work (Persona Mismatch).
EMPLOYER_PERSONA_PATTERNS = [
    r"אנחנו מגייסים", r"אנו מגייסים", r"החברה שלנו מחפשת עובד",
    r"מחפשים עובדים", r"מחפש עובדים", r"מעסיקים חדשים",
    r"בעל העסק", r"בעלת העסק", r"אני מעסיק", r"אנחנו מעסיקים",
    r"looking to hire", r"we are hiring", r"seeking an? employee",
    r"our company is looking for", r"hiring manager", r"posting a job",
]

# Phrases that signal an explicit refusal when found near a job-category keyword.
REFUSAL_PHRASES = [
    "לא מעוניין", "לא מעוניינת", "לא עובד", "לא עובדת", "לא רוצה",
    "אינני מעוניין", "אינני מעוניינת", "לא אוהב", "לא אוהבת",
    "not interested in", "i don't work", "i do not work", "only work in",
]

# Model 1 gate: topic-level credential check only (license/certification/
# permit/etc.) - can't verify the SPECIFIC credential matches since there's
# no structured credentials field, just free text.
MANDATORY_CREDENTIAL_KEYWORDS = [
    "רישיון", "הסמכה", "תעודת הסמכה", "תעודה", "היתר", "רישיון נשק",
    "תעודת הכשרה", "כשירות", "תעודת מקצוע", "הכשרה מקצועית", "אישור מקצועי",
    "license", "certification", "certificate", "permit",
]

# Soft/transferable skill signals used by Model 3.
SOFT_SKILL_KEYWORDS = [
    "אחריות", "אחראי", "אחראית", "אמינות", "אמין", "אמינה",
    "עמידה בלחץ", "עבודה תחת לחץ", "ניהול זמן", "עבודת צוות",
    "יחסי אנוש", "שירותיות", "זמינות", "רצינות", "מוטיבציה",
    "נמרץ", "נמרצת", "יסודי", "יסודית", "דייקן", "דייקנית", "תקשורתי",
    "responsible", "reliable", "team player", "hard worker", "punctual",
    "fast learner", "motivated", "flexible", "customer service",
]

# Aliases for the category dropdown taxonomy (Ai_Engine/Training_Scripts/
# generate_training_data.py - CATEGORIES list). Should stay empty: job and
# candidate categories share the same fixed dropdown, so they already agree
# on wording. Safety net only - don't add entries without confirming with
# the frontend first.
CATEGORY_SYNONYMS = {}


def _canonical_category(raw):
    raw = (raw or "").strip()
    return CATEGORY_SYNONYMS.get(raw, raw)


# The 6 "Simple Jobs" categories from the spec, detected by keyword over
# category+title+description together, not an exact match on job.category -
# real job categories are free text with no enforced taxonomy. Grouped by
# spec category for readability; matching itself is flat.
SIMPLE_JOB_KEYWORDS = [
    # 1. Pet Care ("בעלי חיים" is the official dropdown value)
    "בעלי חיים", "כלב", "כלבים", "דוג ווקר", "דוגווקר",
    "טיולי כלבים", "הליכה עם כלבים", "פינוק חיות",
    # 2. Event Staffing (waiters, basic bartending, ushers, event setup)
    "הפקה ואירועים", "הפקת אירועים", "אירוע", "אירועים", "מלצר", "מלצרית",
    "ברמן", "ברמנית", "הקמת אירוע", "הקמות לאירוע", "דייל", "דיילת",
    "מסעדנות", "הגשה", "קייטרינג",
    # 3. Basic Retail & Customer Service
    "שירות לקוחות", "קמעונאות", "מוכר", "מוכרת", "קופאי", "קופאית",
    "מכירות ואופנה", "עבודה בחנות",
    # 4. General Labor (moving help, packing, simple deliveries)
    "משלוחים ותחבורה", "משלוחים", "שליח", "שליחה", "הובלה", "הובלות",
    "סבל", "אפסנאות", "אפסנאות ולוגיסטיקה", "לוגיסטיקה", "אריזה",
    "העברת רהיטים", "שליחויות",
    # 5. Promotional (flyer distribution, brand ambassadors)
    "קידום מכירות", "דיילת קידום", "חלוקת פליירים", "פליירים", "טעימות",
    "סוכן שטח", "brand ambassador",
    # 6. Basic Cleaning & Maintenance
    "אחזקה", "ניקיון", "תחזוקה", "מנקה", "ניקוי",
]

YEARS_EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\s*(?:שנות ניסיון|שנות נסיון|שנים ניסיון|שנים נסיון|years?\s+of\s+experience|years?\s+experience)",
    re.IGNORECASE,
)


def _contains_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _detect_explicit_refusal(bio_lower, job_keywords):
    """Refusal phrase within ~40 chars of a job-category keyword.

    KNOWN GAP (deferred - see project memory): misses inverted phrasing like
    "not interested... outside of food service", where the negation sits
    next to the candidate's PREFERRED category, not the job's.
    """
    relevant_keywords = [kw.lower() for kw in job_keywords if len(kw) > 1]
    if not relevant_keywords:
        return False
    for phrase in REFUSAL_PHRASES:
        start = 0
        idx = bio_lower.find(phrase, start)
        while idx != -1:
            window = bio_lower[idx: idx + len(phrase) + 40]
            if any(kw in window for kw in relevant_keywords):
                return True
            idx = bio_lower.find(phrase, idx + 1)
    return False


def _extract_years_of_experience(text):
    matches = YEARS_EXPERIENCE_PATTERN.findall(text)
    years = [safe_int(m) for m in matches]
    return max(years) if years else 0


def _extract_critical_requirements(job_json):
    """Model 1 hard gate input - only job.criticalRequirements (short atomic
    tags), never requirements.mandatory_skills (a free-text paragraph in
    this app, not curated tags - substring-matching prose would falsely
    disqualify almost everyone). No-op until a real tag field exists.
    """
    raw_items = safe_list(job_json.get("criticalRequirements", []))

    return [
        item.strip() for item in raw_items
        if isinstance(item, str) and item.strip() and len(item.strip()) <= 40
    ]


# ==========================================
# The Main AI Pipeline Class
# ==========================================

class JobMatcherPipeline:
    def __init__(self):
        print("★★★ CLICKJOB AI PIPELINE (VERSION 9.0 - GATEKEEPER + 60/40 MODEL) ★★★")
        print("Initializing Models...")

        try:
            print("1. Loading RoBERTa (Semantic Engine)...")
            self.roberta = SentenceTransformer('./saved_matching_model')

            print("2. Loading SVM (Confidence Signal)...")
            self.svm = joblib.load("./saved_svm_model.pkl")

            print("3. Loading MLP (Model 2 Base Scorer)...")
            self.mlp = joblib.load("./saved_mlp_model.pkl")

            print("Pipeline is fully loaded and READY!\n" + "=" * 50)
        except Exception as e:
            print(f"CRITICAL ERROR LOADING MODELS: {e}")

    def evaluate_candidate(self, job_json, candidate_json):
        print(f"--> DEBUG: Received Candidate: {candidate_json.get('id', 'unknown')}")
        try:
            # ==========================================
            # 1. Extract Text Data
            # ==========================================
            job_description = str(job_json.get("description", ""))

            # `requirements` may be a plain string or the structured object
            # matchController.js builds - flatten dicts into text, otherwise
            # str(dict) leaks Python syntax straight into the RoBERTa input.
            requirements_raw = job_json.get("requirements", "")
            if isinstance(requirements_raw, dict):
                req_parts = []
                for key in ("mandatory_skills", "languages", "tech_stack", "tools"):
                    req_parts.extend(safe_list(requirements_raw.get(key)))
                job_requirements = " ".join(str(p) for p in req_parts)
            else:
                job_requirements = str(requirements_raw)

            job_text = f"{job_description} {job_requirements}".strip()
            job_category = str(job_json.get("category", "")).strip()
            job_keywords = [kw for kw in job_category.split() if kw]

            # title may arrive flat (job.title, raw Postman testing) or nested
            # under basic_info.job_title (matchController.js's real payload).
            basic_info_raw = job_json.get("basic_info", {})
            job_title = str(job_json.get("title") or (basic_info_raw.get("job_title") if isinstance(basic_info_raw, dict) else "") or "").strip()

            # See SIMPLE_JOB_KEYWORDS above for why this scans category+title+
            # description together instead of trusting job.category alone.
            simple_job_haystack = f"{job_category} {job_title} {job_description}".strip()

            cand_data = candidate_json.get("candidate", candidate_json) if isinstance(candidate_json.get("candidate"), dict) else candidate_json
            candidate_bio = str(cand_data.get("semantic_profile", "")).strip()

            if not candidate_bio:
                candidate_bio = str(cand_data.get("bio", "")).strip()

            candidate_bio_lower = candidate_bio.lower()
            candidate_categories = safe_list(cand_data.get("jobCatagories", []))
            candidate_soft_skills = safe_list(cand_data.get("softSkills", []))
            personal_info = cand_data.get("personal_info", {}) if isinstance(cand_data.get("personal_info"), dict) else {}
            skills_info = cand_data.get("skills", {}) if isinstance(cand_data.get("skills"), dict) else {}

            # ==========================================
            # 2. Extract Basic Features
            # ==========================================
            distance_km = safe_float(cand_data.get("distance_to_job", 5.0))
            search_radius = safe_float(cand_data.get("searchRadius", 50.0))

            # There is no structured "years of experience" field in this app -
            # candidates just describe their experience in free text (bio /
            # uploaded CV, both folded into semantic_profile), so it's read
            # directly out of that text (e.g. "5 שנות ניסיון").
            total_exp_years = _extract_years_of_experience(candidate_bio)
            experience_months = total_exp_years * 12

            # ==========================================
            # STAGE 0: LOCATION HARD FILTER
            # ==========================================
            if distance_km > search_radius:
                return {
                    "score": 0,
                    "reason": f"נפסל - מחוץ לרדיוס החיפוש (מרחק: {distance_km} ק״מ, רדיוס מוגדר: {search_radius} ק״מ)",
                    "Final_Score": 0,
                    "Status": "NO MATCH",
                    "Reason": f"נפסל - מחוץ לרדיוס החיפוש (מרחק: {distance_km} ק״מ, רדיוס מוגדר: {search_radius} ק״מ)",
                    "Breakdown": {
                        "Semantic_Similarity": 0.0,
                        "SVM_Confidence": 0.0,
                        "Model2_Score": 0.0,
                        "Model3_Score": 0.0,
                        "Experience_Months": experience_months,
                        "Is_Simple_Job": False,
                        "Category_Bonus_Applied": False,
                        "Gatekeeper": "LOCATION_OUT_OF_RADIUS",
                    }
                }

            # ==========================================
            # MODEL 1: THE GATEKEEPER
            # ==========================================
            if _contains_any(candidate_bio_lower, EMPLOYER_PERSONA_PATTERNS):
                reason = "נפסל - הפרופיל נראה כמו מעסיק המחפש לגייס עובדים, לא כמו מחפש עבודה"
                return self._disqualified(reason, "PERSONA_MISMATCH", experience_months)

            if _detect_explicit_refusal(candidate_bio_lower, job_keywords):
                reason = "נפסל - המועמד/ת ציין/ה במפורש שאינו/ה מעוניין/ת בסוג עבודה זה"
                return self._disqualified(reason, "EXPLICIT_REFUSAL", experience_months)

            dealbreakers = job_json.get("dealbreakers", {})
            if isinstance(dealbreakers, dict):
                if dealbreakers.get("is_student_only") and not personal_info.get("is_student", False):
                    reason = "נפסל - המשרה מיועדת לסטודנטים בלבד"
                    return self._disqualified(reason, "STUDENT_ONLY", experience_months)

            # Mandatory credential check (license/certification/permit/etc.) -
            # supersedes and broadens the old driving-license-only dealbreaker.
            job_credential_haystack = f"{job_text} {job_title}"
            job_requires_credential = any(kw in job_credential_haystack for kw in MANDATORY_CREDENTIAL_KEYWORDS)
            if job_requires_credential:
                candidate_has_license = bool(safe_list(skills_info.get("licenses", [])))
                candidate_mentions_credential = any(kw in candidate_bio_lower for kw in MANDATORY_CREDENTIAL_KEYWORDS)
                if not candidate_has_license and not candidate_mentions_credential:
                    reason = "נפסל - המשרה דורשת רישיון/הסמכה/תעודה שלא צוינה בפרופיל המועמד/ת"
                    return self._disqualified(reason, "MISSING_CREDENTIAL", experience_months)

            critical_requirements = _extract_critical_requirements(job_json)
            if critical_requirements:
                unmet = [req for req in critical_requirements if req.lower() not in candidate_bio_lower]
                if unmet:
                    reason = f"נפסל - חסרה דרישת סף קריטית: {', '.join(unmet)}"
                    return self._disqualified(reason, "CRITICAL_REQUIREMENT_MISSING", experience_months)

            # ==========================================
            # MODEL 2: SEMANTIC & EXPERIENCE MATCHER (60%)
            # ==========================================
            job_vector = self.roberta.encode(job_text, convert_to_tensor=True)
            candidate_vector = self.roberta.encode(candidate_bio, convert_to_tensor=True)

            sim_score = util.cos_sim(job_vector, candidate_vector).item()
            semantic_similarity = max(0.0, min(1.0, sim_score))

            svm_input = pd.DataFrame(
                [[semantic_similarity, distance_km, experience_months]],
                columns=['Semantic_Similarity', 'Distance_km', 'Experience_Months']
            )
            svm_confidence = self.svm.predict_proba(svm_input)[0][1]

            mlp_input = pd.DataFrame(
                [[semantic_similarity, svm_confidence]],
                columns=['Semantic_Similarity', 'SVM_Confidence']
            )
            raw_mlp_score = float(self.mlp.predict(mlp_input)[0])

            # Reward direct, provable experience (regex-extracted years) on top
            # of the learned semantic/SVM combination.
            experience_bonus = min(15.0, total_exp_years * 3.0)
            model2_score = max(0.0, min(100.0, raw_mlp_score + experience_bonus))

            # The pretrained SVM over-weights raw Experience_Months regardless
            # of domain (e.g. dog-walking experience inflating a backend-dev
            # score) - damp model2 when semantic similarity itself is low.
            # Doesn't fix the underlying model bias; would need retraining.
            if semantic_similarity < 0.3:
                model2_score = model2_score * (semantic_similarity / 0.3)

            # ==========================================
            # MODEL 3: MOTIVATION & SOFT-SKILL BOOSTER (40%)
            # ==========================================
            # Exact equality on canonical forms, not word-overlap: category
            # values are short fixed-taxonomy phrases, so word-splitting is
            # both too loose (generic words collide) and too strict (misses synonyms).
            job_category_canonical = _canonical_category(job_category)
            candidate_categories_canonical = [_canonical_category(c) for c in candidate_categories]
            category_match = bool(job_category_canonical) and job_category_canonical in candidate_categories_canonical
            is_simple_job = any(kw in simple_job_haystack for kw in SIMPLE_JOB_KEYWORDS)

            soft_skill_hits = sum(1 for kw in SOFT_SKILL_KEYWORDS if kw.lower() in candidate_bio_lower)
            soft_skill_hits += len(candidate_soft_skills)

            # Model3_Score is left purely continuous here (no floor applied) so
            # it stays an honest diagnostic signal in the Breakdown - the floor
            # is applied once, below, directly on the final blended score.
            model3_score = min(100.0, 50.0 + min(40.0, soft_skill_hits * 8.0))

            # ==========================================
            # FINAL WEIGHTED SCORE (60% Model 2 / 40% Model 3)
            # ==========================================
            final_ai_score = (0.6 * model2_score) + (0.4 * model3_score)

            # Smooth floor for Simple Jobs: guarantees the spec's 60+/80+
            # minimum without collapsing every weak candidate onto the same
            # number. Only applies below the floor, rescaling the raw score
            # into [floor, floor+15] proportionally - candidates already
            # above the floor keep their own differentiated score.
            if is_simple_job:
                floor_target = 80.0 if category_match else 60.0
                if final_ai_score < floor_target:
                    quality_fraction = min(1.0, max(0.0, final_ai_score / floor_target))
                    final_ai_score = floor_target + quality_fraction * 15.0

            # Passed the gatekeeper -> never report a bare 0 (that value is
            # reserved for disqualification), and cap at 100. Whole numbers
            # only (65, 71, 92, ...) - no decimal points on the final score.
            final_ai_score = int(round(min(100.0, max(1.0, final_ai_score))))

            # ==========================================
            # STATUS MAPPING - 12-tier scale
            # ==========================================
            # Maps continuous scores (1-100) only. A true Model 1 gate failure
            # is a separate path (score=0, Status="NO MATCH", see
            # _disqualified) - that exact string is relied on by
            # matchController.js's isHardRejected check, so no tier below
            # reuses it. The 1-39 tier reads as "disqualified" but isn't a
            # hard gate failure - these results still get returned/displayed.
            if final_ai_score >= 98:
                match_status = "BULLSEYE"
                match_reason = "התאמה מושלמת - הפרופיל תואם כמעט באופן מלא לדרישות המשרה"
            elif final_ai_score >= 95:
                match_status = "NEAR PERFECT"
                match_reason = "כמעט מושלם - התאמה גבוהה מאוד בין הפרופיל למשרה"
            elif final_ai_score >= 90:
                match_status = "VERY STRONG MATCH"
                match_reason = "התאמה חזקה מאוד - ציון גבוה גם בניסיון הישיר וגם בכישורים הרכים"
            elif final_ai_score >= 85:
                match_status = "STRONG MATCH"
                match_reason = "התאמה חזקה - ציון גבוה גם בניסיון הישיר וגם בכישורים הרכים"
            elif final_ai_score >= 80:
                match_status = "VERY SUITABLE"
                match_reason = "מאוד מתאים"
            elif final_ai_score >= 75:
                match_status = "FITS WELL"
                match_reason = "מתאים היטב"
            elif final_ai_score >= 70:
                match_status = "SUITABLE"
                match_reason = "מתאים"
            elif final_ai_score >= 65:
                match_status = "GOOD POTENTIAL"
                match_reason = "פוטנציאל טוב - " + (
                    "התאמת קטגוריה וכישורים רכים טובים מפצים על חוסר ניסיון ישיר" if is_simple_job
                    else "כישורים רכים סבירים, אך ניסיון ישיר בתחום מוגבל"
                )
            elif final_ai_score >= 60:
                match_status = "BASIC POTENTIAL"
                match_reason = "פוטנציאל בסיסי - " + (
                    "משרה פשוטה עם רף כניסה נמוך, אך התאמה ישירה מוגבלת" if is_simple_job
                    else "כישורים רכים בסיסיים, ניסיון ישיר בתחום מוגבל"
                )
            elif final_ai_score >= 50:
                match_status = "WEAK MATCH"
                match_reason = "התאמה חלשה - מעט מאוד עדות לרלוונטיות לתפקיד"
            elif final_ai_score >= 40:
                match_status = "NOT SUITABLE"
                match_reason = "לא מתאים - הפער בין הפרופיל לדרישות המשרה גדול מדי"
            else:
                match_status = "DISQUALIFIED"
                match_reason = "נפסל - אין התאמה משמעותית בין הפרופיל למשרה"

            return {
                "score": final_ai_score,
                "reason": match_reason,
                "Final_Score": final_ai_score,
                "Status": match_status,
                "Reason": match_reason,
                "Breakdown": {
                    "Semantic_Similarity": round(semantic_similarity, 3),
                    "SVM_Confidence": round(svm_confidence, 3),
                    "Model2_Score": round(model2_score, 1),
                    "Model3_Score": round(model3_score, 1),
                    "Experience_Months": experience_months,
                    "Is_Simple_Job": is_simple_job,
                    "Category_Bonus_Applied": category_match,
                }
            }

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"CRASH CAUGHT: {error_trace}")
            return {
                "score": 0,
                "reason": f"PYTHON CRASH: {str(e)}",
                "Final_Score": 0,
                "Status": "REJECTED",
                "Reason": f"PYTHON CRASH: {str(e)}",
                "Breakdown": {}
            }

    @staticmethod
    def _disqualified(reason, gate_name, experience_months):
        return {
            "score": 0,
            "reason": reason,
            "Final_Score": 0,
            "Status": "NO MATCH",
            "Reason": reason,
            "Breakdown": {
                "Semantic_Similarity": 0.0,
                "SVM_Confidence": 0.0,
                "Model2_Score": 0.0,
                "Model3_Score": 0.0,
                "Experience_Months": experience_months,
                "Is_Simple_Job": False,
                "Category_Bonus_Applied": False,
                "Gatekeeper": gate_name,
            }
        }


if __name__ == "__main__":
    print("Run app.py to start the JSON API Server.")