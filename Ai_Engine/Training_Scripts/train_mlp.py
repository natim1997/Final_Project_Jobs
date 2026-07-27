import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.svm import SVC
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# ==========================================
# MLP Neural Network Script (Final Score)
# ==========================================

def main():
    # Define file paths
    dataset_path = "Data/ai_training_dataset.csv"
    roberta_model_path = "./saved_matching_model"
    svm_model_path = "./saved_svm_model.pkl"
    mlp_model_output = "./saved_mlp_model.pkl"

    print("1. Loading RoBERTa and SVM models...")
    try:
        # Load the models we trained in Step 2 and Step 3
        roberta_model = SentenceTransformer(roberta_model_path)
        svm_model = joblib.load(svm_model_path)
    except Exception as e:
        print(f"Error loading previous models: {e}. Make sure you ran train_model.py and train_svm.py first.")
        return

    print(f"2. Loading training dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    print("3. Generating Semantic Similarity (This takes a moment)...")
    # Convert text to vectors to get the RoBERTa score
    embeddings_job = roberta_model.encode(df['Job_Description'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    embeddings_cv = roberta_model.encode(df['CV_Text'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    
    similarities = []
    for i in range(len(df)):
        sim = util.cos_sim(embeddings_job[i], embeddings_cv[i]).item()
        similarities.append(max(0.0, min(1.0, sim)))
    df['Semantic_Similarity'] = similarities

    # Generate simulated features if missing, just like the SVM script
    if 'Distance_km' not in df.columns:
        df['Distance_km'] = np.where(df['Label'] == 1, np.random.uniform(0, 15, len(df)), np.random.uniform(10, 50, len(df)))
    if 'Experience_Months' not in df.columns:
        df['Experience_Months'] = np.where(df['Label'] == 1, np.random.randint(12, 60, len(df)), np.random.randint(0, 24, len(df)))

    print("4. Getting Confidence Scores from SVM Gatekeeper...")
    # We ask the SVM how confident it is about the match
    svm_features = df[['Semantic_Similarity', 'Distance_km', 'Experience_Months']]
    
    # predict_proba gives probability. [:, 1] gets the probability of a MATCH (1.0)
    svm_probabilities = svm_model.predict_proba(svm_features)[:, 1]
    df['SVM_Confidence'] = svm_probabilities

    print("5. Preparing data for MLP Neural Network...")
    # The MLP uses all these 4 features to make the final decision
    mlp_features = ['Semantic_Similarity', 'SVM_Confidence', 'Distance_km', 'Experience_Months']
    X_mlp = df[mlp_features]

    # We create a target 'Final Score' (0 to 100) for the MLP to learn.
    # It gives 50% weight to SVM, 30% to Semantic Similarity, and 10% each to distance/experience.
    target_scores = (df['SVM_Confidence'] * 50) + (df['Semantic_Similarity'] * 30) + (np.clip(df['Experience_Months']/60, 0, 1) * 10) + (np.clip(1 - df['Distance_km']/50, 0, 1) * 10)
    
    # Make sure the final score does not go above 100 or below 0
    y_mlp = np.clip(target_scores, 0, 100)

    # Split data: 80% to learn, 20% to test
    X_train, X_test, y_train, y_test = train_test_split(X_mlp, y_mlp, test_size=0.2, random_state=42)

    print("6. Training MLP Neural Network (Regressor)...")
    # We use MLPRegressor to predict a number from 0 to 100.
    # hidden_layer_sizes=(64, 32) means 2 layers inside the brain with 64 and 32 neurons.
    mlp_model = MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu', solver='adam', max_iter=500, random_state=42)
    mlp_model.fit(X_train, y_train)

    print("\n7. Checking MLP Performance...")
    y_pred = mlp_model.predict(X_test)
    
    # MAE means "Mean Absolute Error". How many points off is the prediction on average?
    mae = mean_absolute_error(y_test, y_pred)
    # R-squared measures accuracy. 1.0 is perfect.
    r2 = r2_score(y_test, y_pred)
    
    print("-" * 40)
    print(f"Average Error (MAE): {mae:.2f} points")
    print(f"Prediction Accuracy (R-squared): {r2:.4f}")
    print("-" * 40)

    print(f"\n8. Saving Final MLP model to {mlp_model_output}...")
    joblib.dump(mlp_model, mlp_model_output)
    print("Success! The ClickJob AI Pipeline is now fully trained!")

if __name__ == "__main__":
    main()