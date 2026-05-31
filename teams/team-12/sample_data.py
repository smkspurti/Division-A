import pandas as pd
import numpy as np
import random

def generate_dirty_titanic(n_records: int = 200) -> pd.DataFrame:
    """
    Generates a highly messy, synthetic Titanic-like dataset.
    Intentionally injects errors across all 6 dimensions of data quality:
    1. Completeness: Missing values in Age, Cabin, Embarked, Fare.
    2. Uniqueness: Exact and near-duplicate rows.
    3. Validity: Invalid ages (<0, >120), invalid survival codes (e.g. 3), and type mismatches.
    4. Consistency: Categorical labeling conflicts (e.g. 'M', 'male', 'Male', 'fem', 'female').
    5. Accuracy: High-leverage outliers in Fare and Age.
    6. Integrity: Mismatch between columns (e.g. child traveling with parents but Parch=0).
    """
    np.random.seed(42)
    random.seed(42)
    
    # 1. Base clean structure
    data = {
        'PassengerId': list(range(1, n_records + 1)),
        'Survived': np.random.choice([0, 1], size=n_records, p=[0.6, 0.4]),
        'Pclass': np.random.choice([1, 2, 3], size=n_records, p=[0.25, 0.25, 0.50]),
        'Name': [f"Passenger, Row_{i}" for i in range(1, n_records + 1)],
        'Sex': np.random.choice(['male', 'female'], size=n_records, p=[0.55, 0.45]),
        'Age': np.random.normal(loc=29.0, scale=14.0, size=n_records).round(1),
        'SibSp': np.random.choice([0, 1, 2, 3], size=n_records, p=[0.7, 0.2, 0.07, 0.03]),
        'Parch': np.random.choice([0, 1, 2], size=n_records, p=[0.8, 0.15, 0.05]),
        'Ticket': [f"PC {random.randint(10000, 99999)}" for _ in range(n_records)],
        'Fare': np.random.exponential(scale=32.0, size=n_records).round(4),
        'Cabin': [f"C{random.randint(1, 148)}" if random.random() > 0.7 else None for _ in range(n_records)],
        'Embarked': np.random.choice(['S', 'C', 'Q'], size=n_records, p=[0.7, 0.2, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Ensure some column types are 'object' initially to represent raw files
    df['Survived'] = df['Survived'].astype(object)
    df['Pclass'] = df['Pclass'].astype(object)
    df['Age'] = df['Age'].astype(object)
    df['Fare'] = df['Fare'].astype(object)
    
    # 2. Inject Completeness Issues (Missing Values / Sentinel Nulls)
    # Age: 20% missing, some as NaNs, some as "?" or "N/A"
    for i in range(0, n_records, 5):
        df.at[i, 'Age'] = np.nan
    for i in range(3, n_records, 15):
        df.at[i, 'Age'] = "?"
    for i in range(7, n_records, 20):
        df.at[i, 'Age'] = "n/a"
        
    # Cabin: 75% missing
    for i in range(n_records):
        if i % 4 != 0:
            df.at[i, 'Cabin'] = np.nan
            
    # Embarked: 3% missing
    for i in range(11, n_records, 33):
        df.at[i, 'Embarked'] = np.nan
        
    # Fare: 5% missing
    for i in range(13, n_records, 20):
        df.at[i, 'Fare'] = "NULL"
        
    # 3. Inject Uniqueness Issues (Duplicates)
    # Inject exact duplicates
    dup_indices = [5, 12, 45, 92, 115]
    for idx in dup_indices:
        dup_row = df.iloc[idx].copy()
        df = pd.concat([df, pd.DataFrame([dup_row])], ignore_index=True)
        
    # Inject near duplicates (same person, slightly different Fare or Age)
    near_dup_row = df.iloc[20].copy()
    near_dup_row['Fare'] = float(near_dup_row['Fare']) + 1.5 if str(near_dup_row['Fare']).replace('.', '', 1).isdigit() else 20.0
    near_dup_row['PassengerId'] = df['PassengerId'].max() + 1
    df = pd.concat([df, pd.DataFrame([near_dup_row])], ignore_index=True)
    
    # 4. Inject Validity Issues (Out of range, type errors)
    # Out of range Age
    df.at[10, 'Age'] = -5.0
    df.at[35, 'Age'] = 150.0
    df.at[62, 'Age'] = 250.0  # extreme outlier
    
    # Invalid Survived values
    df.at[15, 'Survived'] = 3
    df.at[82, 'Survived'] = "Yes"
    df.at[142, 'Survived'] = "unknown"
    
    # Invalid Pclass
    df.at[40, 'Pclass'] = 5
    df.at[99, 'Pclass'] = "First"
    
    # 5. Inject Consistency Issues (Categorical Variants)
    # Sex variations: 'M', 'm', 'male', 'Male', 'FEMALE', 'F', 'f', 'female'
    sex_variants = ['M', 'm', 'male', 'Male', 'FEMALE', 'F', 'f', 'female', 'fem', 'MALE']
    for i in range(len(df)):
        if df.at[i, 'Sex'] == 'male':
            df.at[i, 'Sex'] = random.choice(['male', 'Male', 'M', 'm', 'MALE'])
        else:
            df.at[i, 'Sex'] = random.choice(['female', 'FEMALE', 'F', 'f', 'fem'])
            
    # Embarked variations
    for i in range(len(df)):
        if pd.notna(df.at[i, 'Embarked']):
            if df.at[i, 'Embarked'] == 'S':
                df.at[i, 'Embarked'] = random.choice(['S', 'Southampton', 's'])
            elif df.at[i, 'Embarked'] == 'C':
                df.at[i, 'Embarked'] = random.choice(['C', 'Cherbourg', 'c'])
            elif df.at[i, 'Embarked'] == 'Q':
                df.at[i, 'Embarked'] = random.choice(['Q', 'Queenstown', 'q'])
                
    # 6. Inject Accuracy Issues (Outliers)
    df.at[25, 'Fare'] = 9999.99  # Extreme Fare outlier
    df.at[74, 'Fare'] = -50.0   # Negative Fare
    df.at[110, 'Fare'] = 1500.0  # High Fare outlier
    
    # Reset index and return
    df = df.reset_index(drop=True)
    return df

def save_dirty_titanic(file_path: str, n_records: int = 200) -> None:
    """Generates the dirty titanic dataset and saves it to the specified path."""
    df = generate_dirty_titanic(n_records)
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

def generate_dirty_adult(n_records: int = 500) -> pd.DataFrame:
    np.random.seed(42)
    data = {
        'age': np.random.normal(38, 13, n_records).round(0),
        'workclass': np.random.choice(['Private', 'Self-emp-not-inc', 'Local-gov', '?', 'State-gov'], n_records),
        'fnlwgt': np.random.randint(20000, 500000, n_records),
        'education': np.random.choice(['Bachelors', 'Some-college', '11th', 'HS-grad', 'Prof-school'], n_records),
        'education.num': np.random.choice([9, 10, 13, 14], n_records),
        'marital.status': np.random.choice(['Married-civ-spouse', 'Divorced', 'Never-married'], n_records),
        'occupation': np.random.choice(['Tech-support', 'Craft-repair', 'Other-service', 'Sales', '?'], n_records),
        'relationship': np.random.choice(['Wife', 'Own-child', 'Husband', 'Not-in-family'], n_records),
        'race': np.random.choice(['White', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo', 'Other', 'Black'], n_records),
        'sex': np.random.choice(['Female', 'Male', 'F', 'M', 'm', 'f'], n_records),
        'capital.gain': np.random.exponential(1000, n_records).round(0),
        'capital.loss': np.random.exponential(50, n_records).round(0),
        'hours.per.week': np.random.normal(40, 10, n_records).round(0),
        'native.country': np.random.choice(['United-States', 'Cambodia', 'England', '?', 'Mexico'], n_records),
        'income': np.random.choice(['<=50K', '>50K', '<=50k', '>50k', '50k+'], n_records)
    }
    df = pd.DataFrame(data)
    # Inject errors
    df.loc[5, 'age'] = -10
    df.loc[10, 'age'] = 200
    df.loc[20, 'income'] = np.nan
    df.loc[30:35, 'capital.gain'] = "NULL"
    return df

def generate_dirty_rein(n_records: int = 300) -> pd.DataFrame:
    np.random.seed(42)
    data = {
        'id': list(range(n_records)),
        'title': [f"Item {i}" for i in range(n_records)],
        'price': np.random.uniform(5.0, 500.0, n_records).round(2),
        'category': np.random.choice(['Electronics', 'Books', 'Clothing', 'Home', 'unknown'], n_records),
        'rating': np.random.uniform(1.0, 5.0, n_records).round(1)
    }
    df = pd.DataFrame(data)
    df.loc[0:10, 'rating'] = 9.9
    df.loc[15, 'price'] = -50
    df.loc[20:25, 'title'] = np.nan
    df.loc[30, 'category'] = "Elec"
    return df

def generate_dirty_openrefine(n_records: int = 250) -> pd.DataFrame:
    np.random.seed(42)
    data = {
        'Record_ID': list(range(n_records)),
        'Company_Name': [f"Corp {i}" for i in range(n_records)],
        'Date_Founded': [f"19{random.randint(50,99)}-0{random.randint(1,9)}-1{random.randint(0,9)}" for _ in range(n_records)],
        'Revenue': np.random.randint(10000, 999999, n_records),
        'Employees': np.random.randint(10, 5000, n_records)
    }
    df = pd.DataFrame(data)
    df.loc[1, 'Company_Name'] = df.loc[0, 'Company_Name']
    df.loc[5, 'Employees'] = -10
    df.loc[8, 'Date_Founded'] = "Unknown"
    return df

