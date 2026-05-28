import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_mlp_model(data_path, model_output_path):
    """
    Loads the dataset, filters out unused features, trains an MLP Neural Network,
    evaluates it, and saves the trained model.
    """
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: {data_path} not found.")
        return

    # Separate features (X) from the target label (y)
    # CRITICAL FIX: Explicitly drop features we no longer use in production
    features_to_drop = ['Actual_Label', 'Military_Bonus', 'Education_Score']
    
    # Drop only if they exist in the dataframe to prevent errors
    existing_drops = [col for col in features_to_drop if col in df.columns]
    X = df.drop(columns=existing_drops) 
    y = df['Actual_Label']

    print("Splitting data into 80% training and 20% testing...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Building and training the MLP Neural Network...")
    # hidden_layer_sizes=(8, 4) means two hidden layers with 8 and 4 neurons.
    # We keep it small to prevent overfitting on our 300-row sample.
    mlp_model = MLPClassifier(hidden_layer_sizes=(8, 4), max_iter=2000, random_state=42)
    
    # Train the model
    mlp_model.fit(X_train, y_train)

    print("\nEvaluating the MLP Meta-Learner on test data...")
    y_pred = mlp_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print("-" * 30)
    print(f"MLP Accuracy: {acc * 100:.2f}%")
    print("-" * 30)
    print("\nDetailed Report:")
    print(classification_report(y_test, y_pred))

    print(f"\nSaving the trained MLP model to {model_output_path}...")
    joblib.dump(mlp_model, model_output_path)
    print("Done! The MLP Meta-Learner is ready to judge.")

if __name__ == "__main__":
    # Point to the correct relative paths inside your project structure
    INPUT_CSV = "Data/mlp_training_data.csv"
    OUTPUT_MODEL = "Models/mlp_model.pkl"
    
    train_mlp_model(INPUT_CSV, OUTPUT_MODEL)