"""
utils/data_loader.py
Loads FAO dataset only - WDPSA Post-Harvest Loss Data
"""

import pandas as pd
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path, low_memory=False)
    return pd.DataFrame()


def load_real_fao_data():
    """Load the actual FAO dataset (Data.csv)"""
    df = _load("Data.csv")
    if df.empty:
        return pd.DataFrame()
    return df


def get_loss_data(crop: str) -> pd.DataFrame:
    """Return FAO post-harvest loss rows for a crop."""
    df = load_real_fao_data()
    
    if df.empty:
        # Fallback if CSV not found
        return pd.DataFrame([{"stage": "Post-Harvest", "loss_pct": 2.0}])
    
    # Map crop names
    crop_mapping = {
        "Rice": "Rice",
        "Wheat": "Wheat", 
        "Maize": "Maize",
        "Pulses": "Pulses",
        "Groundnut": "Groundnut"
    }
    
    csv_crop = crop_mapping.get(crop, crop)
    
    if 'commodity' in df.columns:
        mask = df['commodity'].astype(str).str.contains(csv_crop, case=False, na=False)
        matched = df[mask].copy()
        
        if not matched.empty:
            # Get loss percentage
            if 'loss_percentage' in matched.columns:
                matched['loss_pct'] = pd.to_numeric(matched['loss_percentage'], errors='coerce')
            else:
                matched['loss_pct'] = 2.0
            
            # Get stage
            if 'food_supply_stage' in matched.columns:
                matched['stage'] = matched['food_supply_stage'].fillna('Processing')
            elif 'activity' in matched.columns:
                matched['stage'] = matched['activity'].fillna('Processing')
            else:
                matched['stage'] = 'Processing'
            
            # Return only needed columns - NO 'cause' column
            result_df = matched[['stage', 'loss_pct']].copy()
            result_df = result_df.dropna(subset=['loss_pct'])
            
            if not result_df.empty:
                return result_df
    
    # Fallback
    return pd.DataFrame([{"stage": "Processing", "loss_pct": 2.0}])


def get_total_loss_pct(crop: str) -> float:
    """Return cumulative loss % from FAO data."""
    df = get_loss_data(crop)
    if df.empty or 'loss_pct' not in df.columns:
        return 12.5
    
    total = df['loss_pct'].sum()
    # Cap at 16% as per problem statement
    if total > 16:
        total = 16.0
    return round(total, 1)


def get_pest_calendar(crop: str) -> list[dict]:
    """Return pest data."""
    pest_data = {
        "Rice": [
            {"pest": "Stem Borer", "peak_months": "Jun-Sep", "risk": "High",
             "damage": "Dead hearts", "control": "Cartap hydrochloride 4G"},
            {"pest": "Rice Weevil", "peak_months": "Year-round", "risk": "Medium",
             "damage": "Grains hollowed", "control": "Aluminum phosphide"},
        ],
        "Wheat": [
            {"pest": "Termites", "peak_months": "Nov-Jan", "risk": "High",
             "damage": "Root damage", "control": "Chlorpyriphos 20EC"},
            {"pest": "Khapra Beetle", "peak_months": "Storage", "risk": "Severe",
             "damage": "Grain damage", "control": "Methyl bromide"},
        ],
        "Maize": [
            {"pest": "Stem Borer", "peak_months": "Jul-Sep", "risk": "High",
             "damage": "Stalk tunneling", "control": "Granular carbofuran"},
            {"pest": "Weevils", "peak_months": "Year-round", "risk": "Medium",
             "damage": "Holes in grains", "control": "Neem leaves"},
        ],
        "Pulses": [
            {"pest": "Bruchids", "peak_months": "Apr-Jun", "risk": "Severe",
             "damage": "Round holes", "control": "Vegetable oil 5ml/kg"},
        ],
        "Groundnut": [
            {"pest": "Groundnut Beetle", "peak_months": "First 3 months", "risk": "High",
             "damage": "Kernel damage", "control": "CO2 fumigation"},
        ]
    }
    return pest_data.get(crop, [])


def check_scheme_eligibility(crop: str, quantity_kg: float, region: str) -> list[dict]:
    """Return schemes based on government data."""
    schemes = []
    
    if quantity_kg >= 1000:
        schemes.append({
            "scheme_name": "AMIF Warehouse Scheme",
            "authority": "NABARD",
            "subsidy_pct": 25,
            "max_subsidy_lakhs": 100,
            "duration_months": 0,
            "contact": "NABARD: 022-26539800",
            "notes": "25% subsidy for warehouse construction up to Rs 1 crore"
        })
    
    if quantity_kg >= 500 and crop in ["Rice", "Wheat"] and "karnataka" in region.lower():
        schemes.append({
            "scheme_name": "WDPSA Free Storage",
            "authority": "WDRA",
            "subsidy_pct": 0,
            "duration_months": 3,
            "max_subsidy_lakhs": 0,
            "contact": "WDRA: 011-23383370",
            "notes": "Free storage for 3 months in designated warehouses"
        })
    
    schemes.append({
        "scheme_name": "PM-KISAN",
        "authority": "Ministry of Agriculture",
        "subsidy_pct": 0,
        "duration_months": 0,
        "max_subsidy_lakhs": 0,
        "contact": "1800-180-1551",
        "notes": "Rs 6,000/year direct benefit transfer"
    })
    
    return schemes


def get_loss_context_for_prompt(crop: str, quantity_kg: float) -> str:
    """Return FAO loss data for LLM prompt."""
    total_loss = get_total_loss_pct(crop)
    loss_kg = round(quantity_kg * total_loss / 100, 1)
    loss_value = round(loss_kg * 25, 0)
    
    return f"Expected loss without intervention: {total_loss}% ({loss_kg} kg approx Rs {int(loss_value)})"


def get_fao_data_summary() -> str:
    """Return summary of FAO data used."""
    df = load_real_fao_data()
    if df.empty:
        return "FAO Food Loss Database (2022)"
    
    crops = df['commodity'].unique() if 'commodity' in df.columns else []
    return f"FAO Database 2022 - Data loaded"