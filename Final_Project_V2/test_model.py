import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def load_ai_model(model_path="./saved_matching_model"):
    """
    Loads the fine-tuned XLM-RoBERTa model and tokenizer from the local directory.
    """
    print(f"Loading model from {model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        return tokenizer, model
    except Exception as e:
        print(f"Failed to load model. Did you extract the zip file correctly? Error: {e}")
        return None, None

def predict_match_score(tokenizer, model, job_description, cv_text):
    """
    Takes a job description and a CV, feeds them to the model,
    and returns a match probability score (percentage).
    """
    # Tokenize the inputs together
    inputs = tokenizer(
        job_description,
        cv_text,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt" # Return PyTorch tensors
    )
    
    # Run the model (without calculating gradients to save memory)
    with torch.no_grad():
        outputs = model(**inputs)
        
    # The model outputs raw logits. We use softmax to convert them to probabilities.
    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    
    # Class 1 is 'Match', Class 0 is 'No Match'
    # We extract the probability of Class 1 and convert to percentage
    match_probability = probabilities[0][1].item() * 100
    
    return round(match_probability, 2)

if __name__ == "__main__":
    # 1. Load the model
    my_tokenizer, my_model = load_ai_model()
    
    if my_model:
        print("\n--- Testing the AI Model ---\n")
        
        # Test Case A: A very good match
        job_a = "דרוש מפתח Python מתחיל למשרת ג'וניור. נדרשת היכרות עם פיתוח תוכנה, עבודה עם מסדי נתונים ויכולת למידה עצמית."
        cv_a = "סטודנט למדעי המחשב בשנה האחרונה. בעל ניסיון בפיתוח פרויקטים ב-Python, עבודה עם SQL ומוטיבציה גבוהה להשתלב בתעשייה."
        
        score_a = predict_match_score(my_tokenizer, my_model, job_a, cv_a)
        print("Test Case A (Should be High Match):")
        print(f"Job: {job_a}")
        print(f"CV: {cv_a}")
        print(f"Match Score: {score_a}%\n")
        
        # Test Case B: A very bad match
        job_b = "למסעדה יוקרתית בתל אביב דרוש/ה מלצר/ית עם ניסיון. עבודה במשמרות, סביבה צעירה ודינמית. תודעת שירות גבוהה חובה."
        cv_b = "מהנדס חשמל מנוסה. התמחות בתכנון מעגלים מודפסים, עבודה עם תוכנות שרטוט והובלת צוותי חומרה. מחפש משרה ניהולית."
        
        score_b = predict_match_score(my_tokenizer, my_model, job_b, cv_b)
        print("Test Case B (Should be Low Match):")
        print(f"Job: {job_b}")
        print(f"CV: {cv_b}")
        print(f"Match Score: {score_b}%\n")