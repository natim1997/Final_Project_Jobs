# Retrains the SVM on real job data (Data/real_training_dataset.csv) using
# the base (non-fine-tuned) model. Distance/Experience have no real training
# data, so they're random noise here - SVM learns to mostly ignore them.
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def main():
    import os
    dataset_path = "Data/real_training_dataset.csv"
    cached_path = "Data/real_training_dataset_with_similarity.csv"
    svm_model_output = "./saved_svm_model_v2.pkl"

    df = pd.read_csv(dataset_path, encoding="utf-8")

    if os.path.exists(cached_path):
        print(f"1. Reusing cached Semantic_Similarity from {cached_path}...")
        cached = pd.read_csv(cached_path, encoding="utf-8-sig")
        assert len(cached) == len(df), "cached similarity file doesn't match current dataset - delete it to regenerate"
        df['Semantic_Similarity'] = cached['Semantic_Similarity']
        df['Distance_km'] = cached['Distance_km']
        df['Experience_Months'] = cached['Experience_Months']
    else:
        print("1. Loading base (non-fine-tuned) multilingual model...")
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        print(f"2. Generating semantic similarity scores for {len(df)} real pairs (this takes a while on CPU)...")
        embeddings_job = model.encode(df['Job_Description'].tolist(), convert_to_tensor=True, show_progress_bar=True, batch_size=32)
        embeddings_cv = model.encode(df['CV_Text'].tolist(), convert_to_tensor=True, show_progress_bar=True, batch_size=32)
        similarities = []
        for i in range(len(df)):
            sim = util.cos_sim(embeddings_job[i], embeddings_cv[i]).item()
            similarities.append(max(0.0, min(1.0, sim)))
        df['Semantic_Similarity'] = similarities
        rng = np.random.default_rng(42)
        df['Distance_km'] = rng.uniform(0, 50, len(df))
        df['Experience_Months'] = rng.integers(0, 60, len(df))

    features_list = ['Semantic_Similarity', 'Distance_km', 'Experience_Months']
    X = df[features_list]
    y = df['Label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Must scale features first - Distance/Experience are much bigger numbers
    # than Semantic_Similarity, so without scaling they drown it out (measured:
    # 48.7% accuracy unscaled vs 72.5% scaled).
    print("4. Training SVM Classifier (RBF Kernel, with feature scaling)...")
    svm_clf = make_pipeline(StandardScaler(), SVC(kernel='rbf', probability=True, random_state=42))
    svm_clf.fit(X_train, y_train)

    print("\n5. Checking SVM Accuracy:")
    y_pred = svm_clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("-" * 40)
    print(f"SVM Model Accuracy: {accuracy * 100:.2f}%")
    print("-" * 40)
    print(classification_report(y_test, y_pred))

    joblib.dump(svm_clf, svm_model_output)
    print(f"\nSaved retrained SVM to {svm_model_output}")

    df[features_list + ['Label']].to_csv("Data/real_training_dataset_with_similarity.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
