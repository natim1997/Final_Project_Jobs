import re
import pandas as pd
import numpy as np
import joblib
import traceback
from sentence_transformers import SentenceTransformer, util

# ==========================================
# Helper Functions for JSON Data
# ==========================================

def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

def safe_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return list(val.values())
    if isinstance(val, str):
        return [val]
    return []

# ==========================================
# DISPLAY SCORE RESCALE
# ==========================================
# raw_score rarely exceeds ~45 in practice (calibrated on 1,081 real pairs -
# see report ch. 10/11), which reads badly as "68/100". Stretches it onto the
# full 0-100 range via monotonic piecewise-linear interpolation, so ranking
# (and Precision@5) is unchanged - only the displayed number/label shifts.
_RESCALE_ANCHORS = [
    (0, 0),
    (20, 12),
    (27, 38),   # median of real irrelevant pairs
    (33, 60),   # median of real relevant pairs
    (38, 78),   # ~95th percentile of real pairs
    (45, 90),   # ~99th percentile of real pairs
    (88, 100),  # near word-for-word candidate/job text match (measured ceiling)
]


def _rescale_display_score(raw_score):
    raw_score = max(0.0, min(100.0, float(raw_score)))
    xs = [a[0] for a in _RESCALE_ANCHORS]
    ys = [a[1] for a in _RESCALE_ANCHORS]
    if raw_score >= xs[-1]:
        return 100.0
    for i in range(len(xs) - 1):
        if xs[i] <= raw_score <= xs[i + 1]:
            span = xs[i + 1] - xs[i]
            t = (raw_score - xs[i]) / span if span > 0 else 0.0
            return ys[i] + t * (ys[i + 1] - ys[i])
    return 100.0


# Named tiers in 5-point display-score bands, top band reserved for a true
# one-to-one match with the job's stated requirements.
_DISPLAY_TIERS = [
    (97, "התאמה מושלמת", "התאמה מלאה, אחד לאחד, לדרישות המשרה"),
    (92, "התאמה יוצאת דופן", "התאמה כמעט מושלמת לדרישות המשרה"),
    (87, "התאמה מצוינת", "התאמה חזקה מאוד לדרישות המשרה"),
    (82, "התאמה חזקה מאוד", "חפיפה גבוהה עם דרישות המשרה"),
    (77, "התאמה חזקה", "חפיפה טובה עם דרישות המשרה"),
    (72, "התאמה טובה מאוד", "רוב הדרישות המרכזיות מתקיימות"),
    (67, "התאמה טובה", "חלק ניכר מהדרישות המרכזיות מתקיים"),
    (62, "התאמה טובה-סבירה", "התאמה עם כמה פערים לא קריטיים"),
    (57, "התאמה סבירה", "התאמה חלקית עם פערים מסוימים"),
    (52, "התאמה סבירה-חלשה", "התאמה חלקית עם פערים ניכרים"),
    (47, "התאמה חלקית", "עדות מוגבלת להתאמה לתפקיד"),
    (42, "התאמה חלקית-חלשה", "עדות מוגבלת מאוד להתאמה לתפקיד"),
    (37, "התאמה חלשה", "מעט מאוד עדות לרלוונטיות לתפקיד"),
    (32, "התאמה חלשה מאוד", "כמעט ואין עדות לרלוונטיות לתפקיד"),
    (27, "התאמה מוגבלת", "הפער מהדרישות ניכר"),
    (22, "התאמה מוגבלת מאוד", "הפער מהדרישות גדול"),
    (17, "כמעט לא מתאים", "הפער מהדרישות גדול מאוד"),
    (12, "לרוב לא מתאים", "הפרופיל אינו תואם את רוב הדרישות"),
    (7, "לא מתאים", "הפרופיל אינו תואם את דרישות המשרה"),
    (0, "לא מתאים כלל", "אין קשר נראה לעין לדרישות המשרה"),
]


def _display_tier(display_score):
    for threshold, label, reason in _DISPLAY_TIERS:
        if display_score >= threshold:
            return label, reason
    return _DISPLAY_TIERS[-1][1], _DISPLAY_TIERS[-1][2]


# Model3 depends only on the candidate's bio, not the job, so an irrelevant
# job can still score high off Model3 alone (measured: 0.209 similarity still
# rescaled to 91/"excellent"). Below this threshold the *label* is capped -
# score/ranking (and Precision@5) are left untouched, only the shown label.
_GENUINE_RELEVANCE_MIN_SIMILARITY = 0.22
_LABEL_CAP_SCORE_WHEN_NOT_GENUINE = 46


def _capped_tier(display_score, semantic_similarity):
    label, reason = _display_tier(display_score)
    if semantic_similarity < _GENUINE_RELEVANCE_MIN_SIMILARITY:
        capped_label, capped_reason = _display_tier(min(display_score, _LABEL_CAP_SCORE_WHEN_NOT_GENUINE))
        if capped_label != label:
            return capped_label, capped_reason
    return label, reason


# ==========================================
# MODEL 1 — GATEKEEPER: reference data
# ==========================================

# Phrases that mean the profile is an employer, not a job seeker
EMPLOYER_PERSONA_PATTERNS = [
    r"אנחנו מגייסים", r"אנו מגייסים", r"החברה שלנו מחפשת עובד",
    r"מחפשים עובדים", r"מחפש עובדים", r"מעסיקים חדשים",
    r"בעל העסק", r"בעלת העסק", r"אני מעסיק", r"אנחנו מעסיקים",
    r"looking to hire", r"we are hiring", r"seeking an? employee",
    r"our company is looking for", r"hiring manager", r"posting a job",
]

# Phrases that mean the candidate refuses this kind of job
REFUSAL_PHRASES = [
    "לא מעוניין", "לא מעוניינת", "לא עובד", "לא עובדת", "לא רוצה",
    "אינני מעוניין", "אינני מעוניינת", "לא אוהב", "לא אוהבת",
    "not interested in", "i don't work", "i do not work", "only work in",
]

# No structured license/certificate field, so we match keywords in the text.
MANDATORY_CREDENTIAL_KEYWORDS = [
    "רישיון", "הסמכה", "תעודת הסמכה", "תעודה", "היתר", "רישיון נשק",
    "תעודת הכשרה", "כשירות", "תעודת מקצוע", "הכשרה מקצועית", "אישור מקצועי",
    "license", "certification", "certificate", "permit",
]

# Soft skill keywords used by Model 3
SOFT_SKILL_KEYWORDS = [
    "אחריות", "אחראי", "אחראית", "אמינות", "אמין", "אמינה",
    "עמידה בלחץ", "עבודה תחת לחץ", "ניהול זמן", "עבודת צוות",
    "יחסי אנוש", "שירותיות", "זמינות", "רצינות", "מוטיבציה",
    "נמרץ", "נמרצת", "יסודי", "יסודית", "דייקן", "דייקנית", "תקשורתי",
    "responsible", "reliable", "team player", "hard worker", "punctual",
    "fast learner", "motivated", "flexible", "customer service",
]

# Category aliases - empty since job/candidate categories share one dropdown.
CATEGORY_SYNONYMS = {}


def _canonical_category(raw):
    raw = (raw or "").strip()
    return CATEGORY_SYNONYMS.get(raw, raw)


# The 6 "Simple Job" categories from the spec, plus extras found in real data.
SIMPLE_JOB_KEYWORDS = [
    # 1. Pet Care
    "בעלי חיים", "כלב", "כלבים", "דוג ווקר", "דוגווקר",
    "טיולי כלבים", "הליכה עם כלבים", "פינוק חיות",
    # 2. Event Staffing
    "הפקה ואירועים", "הפקת אירועים", "הקמת אירוע", "הקמות לאירוע",
    "מלצר", "מלצרית", "ברמן", "ברמנית", "דייל", "דיילת",
    "מסעדנות", "קייטרינג",
    # 3. Basic Retail & Customer Service
    "שירות לקוחות", "קמעונאות", "קופאי", "קופאית", "סדרן", "סדרנית",
    "מכירות ואופנה", "עבודה בחנות", "שירות ומכירה", "נציג שירות",
    "נציגת שירות",
    # 4. General Labor
    "משלוחים ותחבורה", "משלוחים", "שליח", "שליחה", "שליחויות",
    "סבל", "אפסנאות ולוגיסטיקה", "העברת רהיטים", "אריזה",
    # 5. Promotional
    "קידום מכירות", "דיילת קידום", "חלוקת פליירים", "פליירים", "טעימות",
    "סוכן שטח", "brand ambassador",
    # 6. Basic Cleaning & Maintenance
    "ניקיון", "עבודות ניקיון", "מנקה", "ניקוי",
    # 7. Extra categories added after checking real data
    "מאבטח", "מאבטחת", "שומר", "שומרת", "קב\"ט", "קבט",
    "נהג משלוחים", "נהג חלוקה", "נהג/ת", "סייר אופנוע", "סייר /ת",
    "חלוקת מוצרים", "תמיכה טכנית", "מוקד שירות", "שירות טכני",
    "טכנאי", "מזכיר", "מזכירה", "רכז אדמיניסטרטיבי", "רכזת אדמיניסטרטיבית",
    "פקיד קבלה", "פקידת קבלה", "נציג פיננסי", "נציגה פיננסית",
    "בנקאי טלפוני", "בנקאית טלפונית", "שירות הלוואות", "סוקר טלפוני",
    "סוקרת טלפונית", "בנקאות", "בק אופיס", "back office",
]

YEARS_EXPERIENCE_PATTERN = re.compile(
    r"(\d+)\s*(?:שנות ניסיון|שנות נסיון|שנים ניסיון|שנים נסיון|years?\s+of\s+experience|years?\s+experience)",
    re.IGNORECASE,
)


def _contains_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


GENDER_SLASH_PATTERN = re.compile(r"\s*/[א-ת]{1,3}\b")


def _strip_gender_slash(text):
    # Postings write "רכז /ת אדמיניסטרטיבי /ת" - strip the slash so it doesn't break keyword matching.
    return GENDER_SLASH_PATTERN.sub("", text)


def _detect_explicit_refusal(bio_lower, job_keywords):
    # Refusal word within ~40 chars of a job keyword. Known gap: misses
    # "not interested... except food service" style phrasing.
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
    # Only criticalRequirements (short tags) - mandatory_skills is free text and would reject almost everyone.
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
        print("★★★ CLICKJOB AI PIPELINE (VERSION 10.0 - HYBRID SEMANTIC + KEYWORD MODEL) ★★★")
        print("Initializing Models...")

        try:
            print("1. Loading RoBERTa (Semantic Engine)...")
            # Base pretrained model - our fine-tuned version made real results worse (report ch. 10-11).
            self.roberta = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

            print("2. Loading TF-IDF (Keyword Engine)...")
            self.tfidf = joblib.load("./saved_tfidf_vectorizer.pkl")

            print("3. Loading SVM (Confidence Signal)...")
            self.svm = joblib.load("./saved_svm_model_v2.pkl")

            print("4. Loading MLP (Model 2 Base Scorer)...")
            self.mlp = joblib.load("./saved_mlp_model_v2.pkl")

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

            # requirements can be a plain string or a structured object - flatten either way
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

            # title can be flat (job.title) or nested (basic_info.job_title)
            basic_info_raw = job_json.get("basic_info", {})
            job_title = str(job_json.get("title") or (basic_info_raw.get("job_title") if isinstance(basic_info_raw, dict) else "") or "").strip()

            # Only the opening of the description - a keyword buried deep (e.g. in a perks list) is usually noise.
            job_description_opening = job_description[:150]
            simple_job_haystack = _strip_gender_slash(
                f"{job_category} {job_title} {job_description_opening}".strip()
            )

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

            # No structured "years of experience" field - read it from the bio text (e.g. "5 שנות ניסיון")
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

            # Check for license/certificate requirement
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
            # Title reflects the job's real nature better than the description (often full of perks/filler).
            job_title_vector = self.roberta.encode(job_title, convert_to_tensor=True) if job_title else None
            job_vector = self.roberta.encode(job_text, convert_to_tensor=True)
            candidate_vector = self.roberta.encode(candidate_bio, convert_to_tensor=True)

            full_text_sim = util.cos_sim(job_vector, candidate_vector).item()
            if job_title_vector is not None:
                title_sim = util.cos_sim(job_title_vector, candidate_vector).item()
                dense_sim = (0.6 * title_sim) + (0.4 * full_text_sim)
            else:
                dense_sim = full_text_sim

            # TF-IDF on top of semantic score - catches exact word matches (tool name, license) embeddings can miss.
            job_tfidf_vec = self.tfidf.transform([job_text])
            cand_tfidf_vec = self.tfidf.transform([candidate_bio])
            lexical_sim = float((job_tfidf_vec @ cand_tfidf_vec.T).toarray()[0][0])

            sim_score = (0.5 * dense_sim) + (0.5 * lexical_sim)
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

            # SVM/MLP predate the TF-IDF blend and now hurt results - kept only for the Breakdown, not scoring.
            experience_bonus = min(15.0, total_exp_years * 3.0)
            model2_score = max(0.0, min(100.0, (semantic_similarity * 100.0) + experience_bonus))

            # Pull score down further at very low similarity - stops experience in an unrelated field from inflating it.
            if semantic_similarity < 0.3:
                model2_score = model2_score * (semantic_similarity / 0.3)

            # ==========================================
            # MODEL 3: MOTIVATION & SOFT-SKILL BOOSTER (40%)
            # ==========================================
            # Exact category match, not word overlap - avoids false hits on common words in short labels.
            job_category_canonical = _canonical_category(job_category)
            candidate_categories_canonical = [_canonical_category(c) for c in candidate_categories]
            category_match = bool(job_category_canonical) and job_category_canonical in candidate_categories_canonical
            is_simple_job = any(kw in simple_job_haystack for kw in SIMPLE_JOB_KEYWORDS)

            soft_skill_hits = sum(1 for kw in SOFT_SKILL_KEYWORDS if kw.lower() in candidate_bio_lower)
            soft_skill_hits += len(candidate_soft_skills)

            model3_score = min(100.0, 50.0 + min(40.0, soft_skill_hits * 8.0))

            # ==========================================
            # FINAL WEIGHTED SCORE (60% Model 2 / 40% Model 3)
            # ==========================================
            final_ai_score = (0.6 * model2_score) + (0.4 * model3_score)

            # 0 means disqualified, so real matches never show a bare 0.
            raw_score = int(round(min(100.0, max(1.0, final_ai_score))))

            # ==========================================
            # DISPLAY SCORE + STATUS MAPPING
            # ==========================================
            # See _rescale_display_score/_RESCALE_ANCHORS above - ranking is unaffected, only the shown score/label.
            final_ai_score = int(round(_rescale_display_score(raw_score)))
            match_status, match_reason = _capped_tier(final_ai_score, semantic_similarity)

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
                    "Raw_Score": raw_score,
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
