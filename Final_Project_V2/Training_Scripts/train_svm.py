import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_svm_model(data_path, model_output_path):
    """
    Loads the binary feature dataset, trains an SVM model with probability=True,
    evaluates its accuracy, and saves the trained model to a file.
    """
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: {data_path} not found. Did you run the extractor?")
        return

    # Separate features (X) from the target label (y)
    X = df.drop('Label', axis=1)
    y = df['Label']

    print("Splitting data into 80% training and 20% testing...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training the SVM model...")
    print("Note: Setting probability=True so we can get % confidence scores later.")
    
    # We use a linear kernel because our data is simple binary constraints
    svm_model = SVC(kernel='linear', probability=True, random_state=42)
    svm_model.fit(X_train, y_train)

    print("\nEvaluating the model on test data...")
    y_pred = svm_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print("-" * 30)
    print(f"Accuracy: {acc * 100:.2f}%")
    print("-" * 30)
    print("\nDetailed Report:")
    print(classification_report(y_test, y_pred))

    print(f"\nSaving the trained model to {model_output_path}...")
    joblib.dump(svm_model, model_output_path)
    print("Done! The SVM Gatekeeper is ready.")

if __name__ == "__main__":
    INPUT_CSV = "svm_training_data.csv"
    OUTPUT_MODEL = "svm_model.pkl"
    
    train_svm_model(INPUT_CSV, OUTPUT_MODEL)