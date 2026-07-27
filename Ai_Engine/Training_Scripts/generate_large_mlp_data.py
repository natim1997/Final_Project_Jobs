import pandas as pd
import random

def generate_large_mlp_data(num_samples=5000):
    records = []
    columns = [
        "RoBERTa_Score", "SVM_Confidence", "Hard_Skills_Match", "Location_Score",
        "Work_Model_Score", "Experience_Bonus", "Education_Score", "Languages_Match",
        "Management_Bonus", "Military_Bonus", "Availability_Score", "Mobility_Score",
        "Soft_Skills_Match", "Actual_Label"
    ]

    print("Generating large dataset for MLP...")
    for _ in range(num_samples):
        roberta_score = random.choice([0.0, 1.0])
        label = int(roberta_score)
        
        record = {
            "RoBERTa_Score": roberta_score,
            "SVM_Confidence": random.choice([0.5, 0.5136, 0.4871]),
            "Hard_Skills_Match": random.choice([0.0, 0.3333, 1.0]),
            "Location_Score": random.choice([0.0, 1.0]),
            "Work_Model_Score": random.choice([0.0, 1.0]),
            "Experience_Bonus": random.choice([0.0, 1.0]),
            "Education_Score": random.choice([0.0, 0.5, 1.0]),
            "Languages_Match": random.choice([0.0, 1.0]),
            "Management_Bonus": random.choice([0.0, 0.3333, 0.5, 1.0]),
            "Military_Bonus": random.choice([0.0, 1.0]),
            "Availability_Score": 1.0,
            "Mobility_Score": 1.0,
            "Soft_Skills_Match": random.choice([0.0, 1.0]),
            "Actual_Label": label
        }
        records.append(record)
        
    df = pd.DataFrame(records, columns=columns)
    
    df.to_csv("Data/mlp_training_data.csv", index=False)
    print(f"Successfully generated {num_samples} rows in Data/mlp_training_data.csv")

if __name__ == "__main__":
    generate_large_mlp_data()