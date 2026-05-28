import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)

def prepare_dataset(csv_path):
    """
    Loads the CSV, splits it into training and evaluation sets,
    and converts them into Hugging Face Dataset objects.
    """
    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # We only need the text columns and the label for training
    df = df[['Job_Description', 'CV_Text', 'Label']]

    df = df.rename(columns={'Label': 'label'})
    
    # Split the data: 80% for training, 20% for testing/evaluation
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Convert Pandas DataFrames to Hugging Face Datasets
    train_dataset = Dataset.from_pandas(train_df)
    eval_dataset = Dataset.from_pandas(eval_df)
    
    return train_dataset, eval_dataset

def main():
    # Points directly to the clean generated dataset directory
    dataset_path = "Data/ai_training_dataset.csv"
    model_name = "xlm-roberta-base"
    output_dir = "./saved_matching_model"
    
    # 1. Load data
    train_dataset, eval_dataset = prepare_dataset(dataset_path)
    
    # 2. Initialize the Tokenizer
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize_function(examples):
        """
        Tokenizes the job description and the CV text together.
        """
        return tokenizer(
            examples["Job_Description"], 
            examples["CV_Text"], 
            padding="max_length", 
            truncation=True, 
            max_length=512
        )
        
    print("Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)
    
    # 3. Initialize the Model
    print(f"Loading pre-trained model {model_name}...")
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    
   # 4. Define Training Arguments
    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        save_strategy="no",           
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        load_best_model_at_end=False,  
        save_only_model=True,         
    )
    
    # 5. Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        processing_class=tokenizer,
    )
    
    # 6. Start Training
    print("Starting the training process. This may take a while...")
    trainer.train()
    
    # 7. Save the final fine-tuned model and tokenizer
    print(f"Training complete. Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Model saved successfully!")

if __name__ == "__main__":
    main()