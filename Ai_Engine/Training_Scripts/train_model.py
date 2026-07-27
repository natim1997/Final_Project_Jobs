import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split

MAX_LENGTH = 256

def main():
    dataset_path = "Data/ai_training_dataset.csv"
    # Using the exact multilingual model from our matching pipeline
    model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    output_dir = "./saved_matching_model"

    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    # Split the data: 80% training, 20% validation
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)

    print("Converting dataset to SentenceTransformer format...")
    # Convert Pandas DataFrames to InputExample objects.
    # The label must be a float (1.0 for match, 0.0 for no match) for CosineSimilarityLoss
    train_examples = []
    for _, row in train_df.iterrows():
        train_examples.append(InputExample(
            texts=[str(row['Job_Description']), str(row['CV_Text'])], 
            label=float(row['Label'])
        ))

    print(f"Loading Sentence Transformer model {model_name}...")
    model = SentenceTransformer(model_name)
    model.max_seq_length = MAX_LENGTH

    # DataLoader setup
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

    # CosineSimilarityLoss trains the model to output 768-dim vectors 
    # that are highly similar for matches, and distant for non-matches.
    train_loss = losses.CosineSimilarityLoss(model)

    print("Starting Bi-Encoder training process. This may take a while...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=4,
        warmup_steps=100,
        output_path=output_dir,
        show_progress_bar=True
    )
    
    print(f"Training complete. Fine-tuned model saved successfully to {output_dir}!")

if __name__ == "__main__":
    main()