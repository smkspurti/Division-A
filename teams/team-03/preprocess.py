import pandas as pd

def load_and_clean(filepath):
    # Load CSV
    df = pd.read_csv(filepath)
    
    # Parse dates
    df['Arrival_Date'] = pd.to_datetime(
        df['Arrival_Date'], errors='coerce'
    )
    
    # Drop nulls
    df = df.dropna(subset=['Arrival_Date', 'Modal_Price'])
    
    # Sort
    df = df.sort_values(
        ['Commodity', 'Market', 'Arrival_Date']
    ).reset_index(drop=True)
    
    return df

def get_crop_df(df, crop):
    # Filter by crop
    crop_df = df[df['Commodity'] == crop].copy()
    
    # Aggregate by date (all mandis combined)
    agg_df = crop_df.groupby(
        'Arrival_Date'
    )['Modal_Price'].mean().reset_index()
    
    agg_df = agg_df.rename(columns={
        'Arrival_Date': 'ds',
        'Modal_Price':  'y'
    })
    
    return agg_df

def get_best_mandi(df, crop):
    # Filter crop
    crop_df = df[df['Commodity'] == crop].copy()
    
    # Last 30 days
    last_date = crop_df['Arrival_Date'].max()
    last_30   = crop_df[
        crop_df['Arrival_Date'] >= last_date - pd.Timedelta(days=30)
    ]
    
    # Average price per mandi
    mandi_avg = last_30.groupby(
        ['Market', 'District']
    )['Modal_Price'].mean().reset_index()
    
    mandi_avg = mandi_avg.rename(
        columns={'Modal_Price': 'Avg_Price'}
    )
    
    mandi_avg['Avg_Price'] = mandi_avg['Avg_Price'].round(2)
    
    mandi_avg = mandi_avg.sort_values(
        'Avg_Price', ascending=False
    ).reset_index(drop=True)
    
    return mandi_avg