# Retrains the MLP on real job data. Old version set the target as a fixed
# formula of its own inputs (not real learning) - this version uses the
# real match/no-match label instead, so the MLP learns something real.
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

def main():
    dataset_path = "Data/real_training_dataset.csv"
    cached_path = "Data/real_training_dataset_with_similarity.csv"
    svm_model_path = "./saved_svm_model_v2.pkl"
    mlp_model_output = "./saved_mlp_model_v2.pkl"

    svm_model = joblib.load(svm_model_path)

    if os.path.exists(cached_path):
        print(f"1. Reusing cached Semantic_Similarity from {cached_path} (produced by train_svm_v2.py)...")
        cached = pd.read_csv(cached_path, encoding="utf-8-sig")
        df = pd.read_csv(dataset_path, encoding="utf-8")
        assert len(cached) == len(df), "cached similarity file doesn't match current dataset - regenerate"
        df['Semantic_Similarity'] = cached['Semantic_Similarity']
        df['Distance_km'] = cached['Distance_km']
        df['Experience_Months'] = cached['Experience_Months']
    else:
        print("1. Loading base model (no cache found)...")
        roberta_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        print(f"2. Loading real training dataset from {dataset_path}...")
        df = pd.read_csv(dataset_path, encoding="utf-8")
        print(f"3. Generating semantic similarity for {len(df)} real pairs...")
        embeddings_job = roberta_model.encode(df['Job_Description'].tolist(), convert_to_tensor=True, show_progress_bar=True, batch_size=32)
        embeddings_cv = roberta_model.encode(df['CV_Text'].tolist(), convert_to_tensor=True, show_progress_bar=True, batch_size=32)
        similarities = []
        for i in range(len(df)):
            sim = util.cos_sim(embeddings_job[i], embeddings_cv[i]).item()
            similarities.append(max(0.0, min(1.0, sim)))
        df['Semantic_Similarity'] = similarities
        rng = np.random.default_rng(42)
        df['Distance_km'] = rng.uniform(0, 50, len(df))
        df['Experience_Months'] = rng.integers(0, 60, len(df))

    print("4. Getting SVM confidence scores...")
    svm_features = df[['Semantic_Similarity', 'Distance_km', 'Experience_Months']]
    df['SVM_Confidence'] = svm_model.predict_proba(svm_features)[:, 1]

    print("5. Building graded targets from the real (category-match) label + semantic similarity...")
    # Match -> target 65-100, no match -> 0-40, both scaled by similarity
    # so close-but-wrong pairs score a bit higher than totally unrelated ones.
    is_match = df['Label'] == 1
    target_scores = np.where(
        is_match,
        65.0 + df['Semantic_Similarity'] * 35.0,
        df['Semantic_Similarity'] * 40.0,
    )
    y_mlp = np.clip(target_scores, 0, 100)

    mlp_features = ['Semantic_Similarity', 'SVM_Confidence']
    X_mlp = df[mlp_features]

    X_train, X_test, y_train, y_test = train_test_split(X_mlp, y_mlp, test_size=0.2, random_state=42)

    print("6. Training MLP Neural Network...")
    mlp_model = MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu', solver='adam', max_iter=1000, random_state=42)
    mlp_model.fit(X_train, y_train)

    print("\n7. Checking MLP Performance...")
    y_pred = mlp_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print("-" * 40)
    print(f"Average Error (MAE): {mae:.2f} points")
    print(f"Prediction Accuracy (R-squared): {r2:.4f}")
    print("-" * 40)

    joblib.dump(mlp_model, mlp_model_output)
    print(f"\nSaved retrained MLP to {mlp_model_output}")

if __name__ == "__main__":
    main()
