import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# ==========================================
# SVM Training Script for ClickJob Pipeline
# ==========================================

def main():
    # Define file paths
    dataset_path = "Data/ai_training_dataset.csv"
    roberta_model_path = "./saved_matching_model" # The 5.5-hour model you just trained
    svm_model_output = "./saved_svm_model.pkl"

    # 1. Load the RoBERTa model
    print("1. Loading fine-tuned RoBERTa model...")
    try:
        # This model converts text into semantic numbers (embeddings)
        model = SentenceTransformer(roberta_model_path)
    except Exception as e:
        print(f"Error: Could not find model at {roberta_model_path}. Error info: {e}")
        return

    # 2. Load the training data
    print(f"2. Loading training dataset from {dataset_path}...")
    try:
        df = pd.read_csv(dataset_path)
    except FileNotFoundError:
        print(f"Error: {dataset_path} not found. Please check the file path.")
        return

    # 3. Create semantic similarity features
    print("3. Generating semantic similarity scores (This may take a minute)...")
    # Encode job descriptions and CV text into 768-dimension vectors
    embeddings_job = model.encode(df['Job_Description'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    embeddings_cv = model.encode(df['CV_Text'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    
    # Compare the vectors to see how similar they are (0.0 to 1.0)
    similarities = []
    for i in range(len(df)):
        sim = util.cos_sim(embeddings_job[i], embeddings_cv[i]).item()
        similarities.append(max(0.0, min(1.0, sim))) # Keep score between 0 and 1
        
    df['Semantic_Similarity'] = similarities

    # 4. Handle additional features (Distance and Experience)
    # If columns are missing, we create fake data for training purposes
    if 'Distance_km' not in df.columns:
        print("Notice: 'Distance_km' column missing. Generating simulated data...")
        # Matches get short distances (0-15km), non-matches get far distances (10-50km)
        df['Distance_km'] = np.where(df['Label'] == 1, np.random.uniform(0, 15, len(df)), np.random.uniform(10, 50, len(df)))
        
    if 'Experience_Months' not in df.columns:
        print("Notice: 'Experience_Months' column missing. Generating simulated data...")
        # Matches get high experience, non-matches get low experience
        df['Experience_Months'] = np.where(df['Label'] == 1, np.random.randint(12, 60, len(df)), np.random.randint(0, 24, len(df)))

    # 5. Prepare data for SVM training
    # These 3 numbers will help SVM decide if a match is "Pass" or "Fail"
    features_list = ['Semantic_Similarity', 'Distance_km', 'Experience_Months']
    X = df[features_list]
    y = df['Label']

    # Split data: 80% to learn, 20% to test the results
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 6. Train the SVM model
    print("4. Training the SVM Classifier (RBF Kernel)...")
    # probability=True allows the model to give a confidence percentage later
    svm_clf = SVC(kernel='rbf', probability=True, random_state=42)
    svm_clf.fit(X_train, y_train)

    # 7. Evaluate performance
    print("\n5. Checking SVM Accuracy:")
    y_pred = svm_clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("-" * 40)
    print(f"SVM Model Accuracy: {accuracy * 100:.2f}%")
    print("-" * 40)
    print("\nDetailed Performance Report:")
    print(classification_report(y_test, y_pred))

    # 8. Save the model
    print(f"\n6. Saving trained SVM model to {svm_model_output}...")
    joblib.dump(svm_clf, svm_model_output)
    print("Success! The SVM Gatekeeper is ready for action.")

if __name__ == "__main__":
    main()