import pandas as pd
import random

def generate_svm_gatekeeper_data(num_samples=3000):
    records = []
    
    print("Generating Gatekeeper training data...")
    for _ in range(num_samples):
        meets_age_req = random.choice([0, 1])
        has_required_license = random.choice([0, 1])
        has_health_cert = random.choice([0, 1])
        clean_record = random.choice([0, 1]) 
        
        if meets_age_req == 1 and has_required_license == 1 and clean_record == 1:
            label = 1
        else:
            label = 0
            
        records.append({
            "Meets_Age_Req": meets_age_req,
            "Has_Required_License": has_required_license,
            "Has_Health_Cert": has_health_cert,
            "Clean_Record": clean_record,
            "Label": label
        })
        
    df = pd.DataFrame(records)
    df.to_csv("Data/svm_training_data.csv", index=False)
    print(f"Successfully generated {num_samples} records at Data/svm_training_data.csv")

if __name__ == "__main__":
    generate_svm_gatekeeper_data()