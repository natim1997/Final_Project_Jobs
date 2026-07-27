import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score, f1_score
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer

# Must match the MAX_LENGTH used in train_model.py
MAX_LENGTH = 256


def prepare_eval_dataset(csv_path):
    # Load the data from the csv file
    print("Loading test dataset...")
    df = pd.read_csv(csv_path)

    # Keep only the columns we need for testing
    df = df[['Job_Description', 'CV_Text', 'Label']]
    df = df.rename(columns={'Label': 'label'})

    # Split the data exactly like we did in training
    # The random_state=42 makes sure we test on the exact same 20%
    _, eval_df = train_test_split(df, test_size=0.2, random_state=42)

    # Convert to Hugging Face format
    eval_dataset = Dataset.from_pandas(eval_df, preserve_index=False)
    return eval_dataset


def main():
    # Use the same paths as the training script
    dataset_path = "Data/ai_training_dataset.csv"
    model_path = "./saved_matching_model"

    # 1. Load the evaluation dataset
    eval_dataset = prepare_eval_dataset(dataset_path)

    # 2. Load the trained tokenizer and model
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    # 3. Tokenize the text data
    def tokenize_function(examples):
        # Tokenize job description and cv text together
        return tokenizer(
            examples["Job_Description"],
            examples["CV_Text"],
            padding="max_length",
            truncation=True,
            max_length=MAX_LENGTH
        )

    print("Tokenizing data...")
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)

    # 4. Get predictions from the model
    print("Predicting results... this might take a minute...")
    trainer = Trainer(model=model)
    predictions_output = trainer.predict(tokenized_eval)

    # Get the class with the highest score (0 or 1)
    predictions = np.argmax(predictions_output.predictions, axis=1)
    true_labels = predictions_output.label_ids

    # 5. Calculate all the metrics for the presentation
    cm = confusion_matrix(true_labels, predictions)
    acc = accuracy_score(true_labels, predictions)
    f1 = f1_score(true_labels, predictions)

    # 6. Print the final results to the terminal
    print("\n" + "=" * 40)
    print("RoBERTa EVALUATION RESULTS")
    print("=" * 40)
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 Score: {f1:.4f}\n")

    print("CONFUSION MATRIX (Copy to Presentation):")
    print(f"TN (True Negative): {cm[0][0]} -> Model said NO, and it is NO")
    print(f"FP (False Positive): {cm[0][1]} -> Model said YES, but it is NO")
    print(f"FN (False Negative): {cm[1][0]} -> Model said NO, but it is YES")
    print(f"TP (True Positive): {cm[1][1]} -> Model said YES, and it is YES")
    print("=" * 40)


if __name__ == "__main__":
    main()