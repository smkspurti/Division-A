import pandas as pd
import numpy as np
import random

def generate_messy_sales(n_records=300):
    np.random.seed(123)
    random.seed(123)
    
    # Base data
    dates = [f"2023-05-{random.randint(1,28):02d}" for _ in range(n_records)]
    regions = np.random.choice(["North", "South", "East", "West"], size=n_records, p=[0.3, 0.2, 0.3, 0.2])
    items = np.random.choice(["Laptop", "Phone", "Tablet", "Monitor"], size=n_records)
    prices = {"Laptop": 1200.0, "Phone": 800.0, "Tablet": 450.0, "Monitor": 300.0}
    
    qty = np.random.choice([1, 2, 3, 4, 5], size=n_records, p=[0.6, 0.2, 0.1, 0.05, 0.05])
    
    data = []
    for i in range(n_records):
        item = items[i]
        price = prices[item]
        # Inconsistent region naming
        region = regions[i]
        if random.random() > 0.85:
            region = random.choice([region.lower(), region.upper(), region[:2]])
            
        # Missing values (Completeness)
        qty_val = qty[i]
        if random.random() > 0.9:
            qty_val = np.nan
            
        price_val = price
        if random.random() > 0.95:
            price_val = "NULL"
            
        # Accuracy / Outliers
        if random.random() > 0.97:
            price_val = price * 100 # Huge outlier
        elif random.random() > 0.97:
            price_val = -price # Negative value (Validity/Accuracy)
            
        data.append({
            "Transaction_ID": i + 1000,
            "Date": dates[i],
            "Region": region,
            "Product": item,
            "Price": price_val,
            "Quantity": qty_val,
            "Customer_Email": f"user_{i}@example.com" if random.random() > 0.05 else "N/A"
        })
        
    df = pd.DataFrame(data)
    
    # Exact Duplicates (Uniqueness)
    for idx in [10, 50, 100]:
        df = pd.concat([df, pd.DataFrame([df.iloc[idx]])], ignore_index=True)
        
    # Near duplicates
    near_dup = df.iloc[25].copy()
    near_dup["Price"] = float(near_dup["Price"]) + 5.0 if isinstance(near_dup["Price"], (int, float)) else 500.0
    near_dup["Transaction_ID"] = 9999
    df = pd.concat([df, pd.DataFrame([near_dup])], ignore_index=True)
    
    # Validity - bad email format
    df.loc[12, "Customer_Email"] = "invalid_email_at_domain.com"
    df.loc[45, "Customer_Email"] = "missing@"
    
    # Reset index
    df = df.reset_index(drop=True)
    return df

if __name__ == '__main__':
    df = generate_messy_sales()
    df.to_csv("s:/GenAi_hackthon/data/random_dirty_sales.csv", index=False)
    print("Successfully generated random_dirty_sales.csv with 304 rows.")
