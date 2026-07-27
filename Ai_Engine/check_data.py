import pandas as pd
from collections import Counter
import re

def analyze_dataset():
    csv_path = "Data/ai_training_dataset.csv"
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        # Try without Data/ prefix just in case
        df = pd.read_csv("ai_training_dataset.csv")
        
    print("=" * 40)
    print(f"Dataset Shape: {df.shape}")
    print(f"Columns inside: {df.columns.tolist()}")
    print("-" * 40)
    print("Label Distribution:")
    print(df['Label'].value_counts())
    print("-" * 40)
    
    # Check top keywords in job descriptions for label 1 and label 0
    def get_top_words(texts, num=10):
        all_words = []
        for t in texts:
            words = re.findall(r'\b\w+\b', str(t).lower())
            # filter out simple stop words
            words = [w for w in words if len(w) > 3]
            all_words.extend(words)
        return Counter(all_words).most_common(num)

    print("Top words in MATCHES (Label 1):")
    print(get_top_words(df[df['Label'] == 1]['Job_Description']))
    print("-" * 40)
    print("Top words in NO-MATCHES (Label 0):")
    print(get_top_words(df[df['Label'] == 0]['Job_Description']))
    print("=" * 40)

if __name__ == "__main__":
    analyze_dataset()