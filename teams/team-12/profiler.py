import pandas as pd
import numpy as np
import difflib
import warnings
from scipy import stats
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Tuple

# Suppress pandas datetime parsing UserWarnings
warnings.filterwarnings('ignore', category=UserWarning)

def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Infers the logical data type of each column.
    Types can be: 'Numeric', 'Categorical', 'Text', 'DateTime', 'Boolean'.
    """
    inferred_types = {}
    for col in df.columns:
        # Drop missing values for type inference
        non_null_vals = df[col].dropna()
        if len(non_null_vals) == 0:
            inferred_types[col] = 'Categorical'  # Default fallback
            continue
            
        # Check if Boolean
        unique_vals = non_null_vals.unique()
        if len(unique_vals) <= 2:
            # Check if values are boolean-like
            unique_set = {str(v).lower().strip() for v in unique_vals}
            if unique_set.issubset({'0', '1', '0.0', '1.0', 'true', 'false', 'yes', 'no', 'y', 'n', 't', 'f'}):
                inferred_types[col] = 'Boolean'
                continue
                
        # Try numeric conversion
        try:
            pd.to_numeric(non_null_vals)
            inferred_types[col] = 'Numeric'
            continue
        except (ValueError, TypeError):
            pass
            
        # Try DateTime conversion
        # We check if it is string first
        if non_null_vals.dtype == object or isinstance(non_null_vals.iloc[0], str):
            try:
                # Only infer datetime if it's successfully parsed and looks like a date
                # (e.g., has dashes or slashes and parses)
                sample_str = str(non_null_vals.iloc[0])
                if any(char in sample_str for char in ['-', '/', ':']) and len(sample_str) >= 6:
                    pd.to_datetime(non_null_vals, errors='raise')
                    inferred_types[col] = 'DateTime'
                    continue
            except Exception:
                pass
                
        # Categorical vs Text based on uniqueness ratio
        uniqueness_ratio = len(unique_vals) / len(non_null_vals)
        if uniqueness_ratio < 0.15 or len(unique_vals) < 25:
            inferred_types[col] = 'Categorical'
        else:
            inferred_types[col] = 'Text'
            
    return inferred_types

def detect_outliers_iqr(col_series: pd.Series) -> pd.Series:
    """Returns a boolean mask where True indicates an outlier based on IQR."""
    numeric_series = pd.to_numeric(col_series, errors='coerce')
    if numeric_series.dropna().empty:
        return pd.Series(False, index=col_series.index)
    Q1 = numeric_series.quantile(0.25)
    Q3 = numeric_series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return (numeric_series < lower_bound) | (numeric_series > upper_bound)

def detect_outliers_zscore(col_series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Returns a boolean mask where True indicates an outlier based on Z-score."""
    numeric_series = pd.to_numeric(col_series, errors='coerce')
    non_null = numeric_series.dropna()
    if non_null.empty or non_null.std() == 0:
        return pd.Series(False, index=col_series.index)
    mean = non_null.mean()
    std = non_null.std()
    z_scores = (numeric_series - mean) / std
    return z_scores.abs() > threshold

def detect_multivariate_outliers(df: pd.DataFrame, num_cols: List[str]) -> pd.Series:
    """Runs Isolation Forest to detect multivariate outliers across numeric columns."""
    if not num_cols or len(df) < 10:
        return pd.Series(False, index=df.index)
        
    # Copy and impute temporarily for Isolation Forest
    temp_df = df[num_cols].copy()
    for col in num_cols:
        temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce')
        median_val = temp_df[col].median()
        temp_df[col] = temp_df[col].fillna(median_val if pd.notna(median_val) else 0)
        
    try:
        # Fit Isolation Forest
        clf = IsolationForest(contamination=0.03, random_state=42)
        preds = clf.fit_predict(temp_df)
        return pd.Series(preds == -1, index=df.index)
    except Exception:
        return pd.Series(False, index=df.index)

def find_categorical_inconsistencies(df: pd.DataFrame, cat_cols: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Finds casing and fuzzy spelling inconsistencies in categorical columns.
    Returns a dictionary of column -> {invalid_label: dominant_label}.
    """
    inconsistencies = {}
    for col in cat_cols:
        vals = df[col].dropna().astype(str).unique()
        if len(vals) <= 1:
            continue
            
        # Group by case-insensitive, stripped normalized form
        groups = {}
        for v in vals:
            norm = v.strip().lower()
            if norm not in groups:
                groups[norm] = []
            groups[norm].append(v)
            
        # Find casing inconsistencies (same lower-cased value, multiple raw values)
        col_map = {}
        
        # Now do fuzzy matching among the normalized forms
        norm_vals = list(groups.keys())
        fuzzy_groups = {}
        visited = set()
        
        for i, v1 in enumerate(norm_vals):
            if v1 in visited:
                continue
            cluster = [v1]
            visited.add(v1)
            for v2 in norm_vals[i+1:]:
                if v2 in visited:
                    continue
                # Compare similarity using difflib
                sim = difflib.SequenceMatcher(None, v1, v2).ratio()
                is_abbr = (len(v1) == 1 and v2.startswith(v1)) or (len(v2) == 1 and v1.startswith(v2))
                if sim > 0.82 or is_abbr:
                    cluster.append(v2)
                    visited.add(v2)
                    
            if len(cluster) > 1:
                # The dominant normalized value is the one with the highest frequency
                freqs = {}
                for c in cluster:
                    freqs[c] = df[col].astype(str).str.strip().str.lower().eq(c).sum()
                dominant_norm = max(freqs, key=freqs.get)
                fuzzy_groups[dominant_norm] = cluster
                
        # Map raw inconsistent categories to the dominant raw category
        # First process the fuzzy clusters
        for dom_norm, norm_cluster in fuzzy_groups.items():
            raw_vals = []
            for n in norm_cluster:
                raw_vals.extend(groups[n])
            # Find frequencies of raw values
            raw_freqs = {r: df[col].eq(r).sum() for r in raw_vals}
            dom_raw = max(raw_freqs, key=raw_freqs.get)
            for r in raw_vals:
                if r != dom_raw:
                    col_map[r] = dom_raw
                    
        # Now process any casing-only groups not caught in fuzzy clusters
        for norm_val, raw_list in groups.items():
            is_covered = any(v in col_map for v in raw_list)
            if len(raw_list) > 1 and not is_covered:
                raw_freqs = {r: df[col].eq(r).sum() for r in raw_list}
                dom_raw = max(raw_freqs, key=raw_freqs.get)
                for r in raw_list:
                    if r != dom_raw:
                        col_map[r] = dom_raw
                        
        if col_map:
            inconsistencies[col] = col_map
            
    return inconsistencies

def compute_correlation_matrix(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes Pearson correlation matrix for all numeric columns.
    Returns dict with 'columns', 'matrix' (2D list), and 'strong_correlations' (list of notable pairs).
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        return {'columns': numeric_cols, 'matrix': [], 'strong_correlations': []}
    
    corr_matrix = df[numeric_cols].corr()
    
    # Find strong correlations (|r| > 0.5, excluding self-correlation)
    strong = []
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i < j:  # Upper triangle only
                r = corr_matrix.loc[col1, col2]
                if abs(r) > 0.5:
                    strong.append({
                        'col1': col1, 
                        'col2': col2, 
                        'correlation': round(float(r), 3),
                        'strength': 'Strong' if abs(r) > 0.7 else 'Moderate'
                    })
    
    return {
        'columns': numeric_cols,
        'matrix': corr_matrix.round(3).values.tolist(),
        'strong_correlations': sorted(strong, key=lambda x: abs(x['correlation']), reverse=True)
    }


def generate_recommendations(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generates smart cleaning recommendations based on profiling results.
    Returns list of dicts with 'column', 'action', 'reason', 'priority'.
    """
    recommendations = []
    
    for col_name, col_info in profile['columns'].items():
        null_pct = col_info.get('null_pct', 0)
        inferred_type = col_info.get('inferred_type', 'Unknown')
        unique_count = col_info.get('unique_count', 0)
        total = col_info.get('total_count', 1)
        outliers = col_info.get('outliers_count', 0)
        
        # High missing: recommend drop
        if null_pct > 70:
            recommendations.append({
                'column': col_name,
                'action': 'Drop Column',
                'reason': f'{null_pct:.1f}% missing values — too sparse for reliable imputation',
                'priority': 'High',
                'icon': '🗑️'
            })
        # Moderate missing: recommend impute
        elif null_pct > 5:
            method = 'median imputation' if inferred_type == 'Numeric' else 'mode imputation'
            recommendations.append({
                'column': col_name,
                'action': f'Impute Missing ({method})',
                'reason': f'{null_pct:.1f}% missing — {method} preserves distribution',
                'priority': 'High' if null_pct > 20 else 'Medium',
                'icon': '🔧'
            })
        
        # Outliers detected
        if outliers > 0 and inferred_type == 'Numeric':
            outlier_pct = (outliers / total) * 100 if total > 0 else 0
            recommendations.append({
                'column': col_name,
                'action': 'Cap Outliers (IQR)',
                'reason': f'{outliers} outliers detected ({outlier_pct:.1f}%) — clamp to IQR bounds',
                'priority': 'Medium',
                'icon': '📊'
            })
        
        # Type mismatch
        if inferred_type == 'Numeric' and col_info.get('dtype', '') == 'object':
            recommendations.append({
                'column': col_name,
                'action': 'Convert to Numeric',
                'reason': 'Column contains numeric data stored as text — type coercion needed',
                'priority': 'High',
                'icon': '🔄'
            })
        
        # Low uniqueness in non-ID column
        if unique_count == 1 and total > 10:
            recommendations.append({
                'column': col_name,
                'action': 'Drop Column (Constant)',
                'reason': 'Single unique value — provides no analytical signal',
                'priority': 'Low',
                'icon': '🗑️'
            })
    
    # Check for consistency issues from profile
    for issue in profile.get('issues', []):
        if issue.get('dimension') == 'Consistency' and 'column' in issue:
            recommendations.append({
                'column': issue['column'],
                'action': 'Standardize Categories',
                'reason': issue.get('description', 'Inconsistent category labels detected'),
                'priority': 'Medium',
                'icon': '✏️'
            })
    
    # Check for duplicates
    if profile.get('dimension_scores', {}).get('Uniqueness', 100) < 100:
        recommendations.append({
            'column': '(All Columns)',
            'action': 'Remove Duplicates',
            'reason': 'Duplicate rows detected — deduplicate to ensure data integrity',
            'priority': 'Medium',
            'icon': '🧹'
        })
    
    # Sort by priority
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return recommendations


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Profiles a dataset across 6 quality dimensions and generates a
    detailed quality profile with statistical summaries.
    """
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols
    
    # 1. Infer Column Types
    col_types = infer_column_types(df)
    num_cols = [c for c, t in col_types.items() if t == 'Numeric']
    cat_cols = [c for c, t in col_types.items() if t == 'Categorical']
    bool_cols = [c for c, t in col_types.items() if t == 'Boolean']
    
    # Initialize issue log
    issues = []
    
    # ----------------------------------------------------
    # D1 & D2: Dimensions scoring and issue logging
    # ----------------------------------------------------
    
    # 1. COMPLETENESS (Missing values)
    null_matrix = df.isna()
    total_nulls = null_matrix.sum().sum()
    completeness_score = 100.0 * (1.0 - total_nulls / total_cells) if total_cells > 0 else 100.0
    
    # Column-level null counts & issues
    null_by_col = df.isna().sum()
    for col in df.columns:
        null_count = null_by_col[col]
        if null_count > 0:
            pct = (null_count / n_rows) * 100
            severity = 'High' if pct > 40 else ('Medium' if pct > 5 else 'Low')
            issues.append({
                "dimension": "Completeness",
                "column": col,
                "severity": severity,
                "description": f"Column '{col}' has {null_count} missing values ({pct:.1f}%).",
                "affected_rows_count": int(null_count)
            })
            
    # 2. UNIQUENESS (Duplicates)
    # Exclude typical unique ID columns from duplicate row checks
    id_cols = [c for c in df.columns if (c.lower() in ['passengerid', 'id', 'uuid', 'index', 'pk', 'key']) or (df[c].dropna().nunique() == len(df) and pd.api.types.is_numeric_dtype(df[c]) and 'name' not in c.lower() and 'ticket' not in c.lower() and len(df) > 5)]
    df_for_dup = df.drop(columns=id_cols) if id_cols else df
    dup_rows_mask = df_for_dup.duplicated(keep='first')
    dup_rows_count = dup_rows_mask.sum()
    uniqueness_score = 100.0 * (1.0 - dup_rows_count / n_rows) if n_rows > 0 else 100.0
    
    if dup_rows_count > 0:
        pct = (dup_rows_count / n_rows) * 100
        severity = 'High' if pct > 10 else ('Medium' if pct > 2 else 'Low')
        issues.append({
            "dimension": "Uniqueness",
            "column": "Multiple",
            "severity": severity,
            "description": f"Dataset contains {dup_rows_count} duplicate records ({pct:.1f}%).",
            "affected_rows_count": int(dup_rows_count)
        })
        
    # 3. VALIDITY (Type and domain constraints)
    invalid_count = 0
    non_null_cells = total_cells - total_nulls
    
    # Auto-inferred Domain and Type Constraints
    for col in df.columns:
        if col in id_cols:
            continue
        non_null_col = df[col].dropna()
        if non_null_col.empty:
            continue
            
        col_invalid = 0
        desc = ""
        col_lower = col.lower()
        target_type = col_types[col]
        
        # 1. Specially-named standard columns (Age, Fare, Survived, Pclass) for domain validation
        if col_lower == 'survived' or (target_type == 'Boolean' and col_lower != 'sex'):
            # Must be binary 0 or 1-like
            bad_mask = ~non_null_col.astype(str).str.strip().str.replace('.0', '', regex=False).isin(['0', '1', 'True', 'False', 'true', 'false'])
            col_invalid = bad_mask.sum()
            desc = f"Column '{col}' has {col_invalid} invalid binary values outside [0, 1]."
        elif col_lower == 'pclass':
            # Must be 1, 2, or 3
            bad_mask = ~non_null_col.astype(str).str.strip().str.replace('.0', '', regex=False).isin(['1', '2', '3'])
            col_invalid = bad_mask.sum()
            desc = f"Column '{col}' has {col_invalid} invalid classes outside [1, 2, 3]."
        elif 'age' in col_lower:
            # Must be numeric and between 0 and 120
            numeric_col = pd.to_numeric(non_null_col, errors='coerce')
            type_errors = numeric_col.isna().sum()
            range_errors = ((numeric_col < 0) | (numeric_col > 120)).sum()
            col_invalid = type_errors + range_errors
            desc = f"Column '{col}' has {type_errors} type mismatches and {range_errors} values outside logical age [0, 120]."
        elif 'fare' in col_lower or 'price' in col_lower or 'cost' in col_lower:
            # Must be numeric and >= 0
            numeric_col = pd.to_numeric(non_null_col, errors='coerce')
            type_errors = numeric_col.isna().sum()
            range_errors = (numeric_col < 0).sum()
            col_invalid = type_errors + range_errors
            desc = f"Column '{col}' has {type_errors} type mismatches and {range_errors} negative values."
        else:
            # 2. General type validation based on statistical profiles
            if target_type == 'Numeric':
                numeric_col = pd.to_numeric(non_null_col, errors='coerce')
                type_errors = numeric_col.isna().sum()
                
                # Check for range violation (e.g. if >99% of values are >=0, then any negative values are invalid)
                range_errors = 0
                non_null_num = numeric_col.dropna()
                if not non_null_num.empty:
                    is_non_negative = (non_null_num >= 0).mean() >= 0.99
                    if is_non_negative:
                        range_errors = (non_null_num < 0).sum()
                        
                col_invalid = type_errors + range_errors
                desc = f"Column '{col}' has {type_errors} type mismatches and {range_errors} range violations."
            elif target_type == 'Boolean':
                bool_vals = {'0', '1', '0.0', '1.0', 'true', 'false', 'yes', 'no', 'y', 'n', 't', 'f'}
                bad_mask = ~non_null_col.astype(str).str.strip().str.lower().isin(bool_vals)
                col_invalid = bad_mask.sum()
                desc = f"Column '{col}' has {col_invalid} values that fail boolean type conformance."
            elif target_type == 'Categorical':
                # If a categorical column is mostly numeric strings (like codes) and has small number of unique ints (<=5)
                # verify if any values violate these integer categories.
                try:
                    num_series = pd.to_numeric(non_null_col, errors='coerce')
                    if num_series.notna().mean() > 0.8:
                        unique_ints = num_series.dropna().astype(int).unique()
                        if len(unique_ints) <= 5:
                            bad_mask = ~non_null_col.astype(str).str.strip().str.replace('.0', '', regex=False).isin([str(x) for x in unique_ints])
                            col_invalid = bad_mask.sum()
                            desc = f"Column '{col}' has {col_invalid} invalid levels outside expected set {list(unique_ints)}."
                except Exception:
                    pass
                
        if col_invalid > 0:
            invalid_count += col_invalid
            pct = (col_invalid / len(non_null_col)) * 100
            severity = 'High' if pct > 10 else ('Medium' if pct > 1 else 'Low')
            issues.append({
                "dimension": "Validity",
                "column": col,
                "severity": severity,
                "description": desc,
                "affected_rows_count": int(col_invalid)
            })
            
    validity_score = 100.0 * (1.0 - invalid_count / non_null_cells) if non_null_cells > 0 else 100.0
    
    # 4. CONSISTENCY (Categorical representations)
    inconsistencies = find_categorical_inconsistencies(df, cat_cols)
    total_inconsistent_values = 0
    
    for col, mappings in inconsistencies.items():
        # Count how many records have inconsistent values (i.e. values mapped in mappings)
        col_inconsistent_count = df[col].isin(mappings.keys()).sum()
        total_inconsistent_values += col_inconsistent_count
        
        if col_inconsistent_count > 0:
            pct = (col_inconsistent_count / n_rows) * 100
            severity = 'Medium' if pct > 5 else 'Low'
            issues.append({
                "dimension": "Consistency",
                "column": col,
                "severity": severity,
                "description": f"Column '{col}' has {col_inconsistent_count} inconsistent representations (e.g. {list(mappings.keys())[:3]} -> '{list(mappings.values())[0]}').",
                "affected_rows_count": int(col_inconsistent_count)
            })
            
    consistency_score = 100.0 * (1.0 - total_inconsistent_values / non_null_cells) if non_null_cells > 0 else 100.0
    
    # 5. ACCURACY (Outliers)
    outliers_by_col = {}
    total_outliers = 0
    total_numeric_elements = 0
    
    # Detect outliers column by column (using IQR and Z-Score consensus)
    for col in num_cols:
        if col in id_cols:
            continue
        non_null_col = pd.to_numeric(df[col], errors='coerce').dropna()
        if non_null_col.empty:
            continue
            
        total_numeric_elements += len(non_null_col)
        
        # Consensual Outliers: Outlier by IQR and Z-score (standard is IQR, we check both)
        iqr_mask = detect_outliers_iqr(df[col])
        zscore_mask = detect_outliers_zscore(df[col], threshold=3.0)
        
        # Outlier counts: intersection of both masks represents true consensus
        outlier_mask = iqr_mask & zscore_mask
        outliers_count = outlier_mask.sum()
        outliers_by_col[col] = outlier_mask
        total_outliers += outliers_count
        
        if outliers_count > 0:
            pct = (outliers_count / len(non_null_col)) * 100
            severity = 'High' if pct > 8 else ('Medium' if pct > 2 else 'Low')
            # Don't flag high fare as critical unless extreme, standard for Titanic
            if col.lower() == 'fare' and df[col].astype(float).max() < 600:
                severity = 'Low'  # High fares are common in Titanic (up to $512)
            issues.append({
                "dimension": "Accuracy",
                "column": col,
                "severity": severity,
                "description": f"Column '{col}' has {outliers_count} outliers ({pct:.1f}%). Max value: {non_null_col.max()}, Min value: {non_null_col.min()}.",
                "affected_rows_count": int(outliers_count)
            })
            
    # Include multivariate outliers if we have multiple numeric columns
    multivariate_outliers_count = 0
    if len(num_cols) >= 2:
        m_outliers = detect_multivariate_outliers(df, num_cols)
        multivariate_outliers_count = m_outliers.sum()
        if multivariate_outliers_count > 0:
            issues.append({
                "dimension": "Accuracy",
                "column": "Multiple",
                "severity": "Medium",
                "description": f"Detected {multivariate_outliers_count} multivariate outlier records using Isolation Forest.",
                "affected_rows_count": int(multivariate_outliers_count)
            })
            
    accuracy_score = 100.0 * (1.0 - total_outliers / total_numeric_elements) if total_numeric_elements > 0 else 100.0
    
    # 6. INTEGRITY (Logical/Structural soundness)
    integrity_violations = 0
    
    # Verify unique ID columns
    for col in id_cols:
        non_null_col = df[col].dropna()
        if len(non_null_col) != non_null_col.nunique():
            viol = len(non_null_col) - non_null_col.nunique()
            integrity_violations += viol
            issues.append({
                "dimension": "Integrity",
                "column": col,
                "severity": "High",
                "description": f"Identifier column '{col}' is not unique. Found {viol} duplicate IDs.",
                "affected_rows_count": int(viol)
            })
            
    # Titanic Logical Rules Check
    # Rule A: Age vs Parch (A baby cannot travel without parents, e.g. Age < 1, Parch == 0 is highly suspicious)
    if 'Age' in df.columns and 'Parch' in df.columns:
        try:
            age_num = pd.to_numeric(df['Age'], errors='coerce')
            parch_num = pd.to_numeric(df['Parch'], errors='coerce')
            baby_violation = ((age_num < 1) & (parch_num == 0) & age_num.notna()).sum()
            if baby_violation > 0:
                integrity_violations += baby_violation
                issues.append({
                    "dimension": "Integrity",
                    "column": "Age/Parch",
                    "severity": "Low",
                    "description": f"Logical violation: {baby_violation} infants (Age < 1) are traveling without parents (Parch = 0).",
                    "affected_rows_count": int(baby_violation)
                })
        except Exception:
            pass
            
    # Rule B: Fare vs Pclass (Negative fares)
    if 'Fare' in df.columns:
        try:
            fare_num = pd.to_numeric(df['Fare'], errors='coerce')
            neg_fare = (fare_num < 0).sum()
            if neg_fare > 0:
                integrity_violations += neg_fare
                # Note: already flagged in Validity, but also represents Integrity constraint violation
        except Exception:
            pass
            
    integrity_score = 100.0 * (1.0 - integrity_violations / n_rows) if n_rows > 0 else 100.0
    
    # Overall Quality Score - Weighted Harmonic mean of the 6 dimensions
    # Pre-empt division by zero by setting a floor of 1.0 on scores
    dimension_scores = {
        "Completeness": completeness_score,
        "Uniqueness": uniqueness_score,
        "Validity": validity_score,
        "Consistency": consistency_score,
        "Accuracy": accuracy_score,
        "Integrity": integrity_score
    }
    
    weights = {
        "Completeness": 1.5,
        "Uniqueness": 1.0,
        "Validity": 1.5,
        "Consistency": 1.0,
        "Accuracy": 1.2,
        "Integrity": 0.8
    }
    
    numerator = sum(weights.values())
    denominator = sum(weights[dim] / max(dimension_scores[dim], 1.0) for dim in weights)
    overall_score = numerator / denominator
    
    # Build column profiles
    columns_profile = {}
    for col in df.columns:
        non_null_col = df[col].dropna()
        columns_profile[col] = {
            "total_count": int(n_rows),
            "dtype": str(df[col].dtype),
            "inferred_type": col_types[col],
            "null_count": int(null_by_col[col]),
            "null_pct": float((null_by_col[col] / n_rows) * 100),
            "unique_count": int(non_null_col.nunique()),
            "is_outlier_prone": col in num_cols
        }
        
        # Add basic stats
        if col_types[col] == 'Numeric':
            num_series = pd.to_numeric(df[col], errors='coerce').dropna()
            if not num_series.empty:
                columns_profile[col].update({
                    "mean": float(num_series.mean()),
                    "median": float(num_series.median()),
                    "min": float(num_series.min()),
                    "max": float(num_series.max()),
                    "std": float(num_series.std()),
                    "skew": float(num_series.skew() if len(num_series) > 2 else 0),
                    "outliers_count": int(outliers_by_col.get(col, pd.Series(False)).sum())
                })
        elif col_types[col] in ['Categorical', 'Boolean']:
            top_vals = non_null_col.value_counts().head(5).to_dict()
            columns_profile[col].update({
                "top_values": {str(k): int(v) for k, v in top_vals.items()}
            })
            
    # Computes numerical correlations
    correlations = {}
    if len(num_cols) >= 2:
        try:
            num_df = df[num_cols].apply(pd.to_numeric, errors='coerce')
            corrs = num_df.corr().fillna(0).to_dict()
            correlations = {k: {sk: float(sv) for sk, sv in v.items()} for k, v in corrs.items()}
        except Exception:
            pass
            
    result = {
        "summary": {
            "rows": int(n_rows),
            "columns": int(n_cols),
            "total_cells": int(total_cells),
            "total_nulls": int(total_nulls),
            "duplicate_rows": int(dup_rows_count),
        },
        "dimension_scores": {
            "Completeness": float(completeness_score),
            "Uniqueness": float(uniqueness_score),
            "Validity": float(validity_score),
            "Consistency": float(consistency_score),
            "Accuracy": float(accuracy_score),
            "Integrity": float(integrity_score)
        },
        "overall_score": float(overall_score),
        "columns": columns_profile,
        "issues": sorted(issues, key=lambda x: {'High': 0, 'Medium': 1, 'Low': 2}[x['severity']]),
        "correlations": correlations,
        "inconsistent_groups": inconsistencies
    }

    # Add correlation matrix and recommendations
    result['correlation_matrix'] = compute_correlation_matrix(df)
    result['recommendations'] = generate_recommendations(result)

    return result

def compare_profiles(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares before and after profiling results to produce comparison metrics.
    """
    dimension_deltas = {}
    for dim in before["dimension_scores"]:
        b_score = before["dimension_scores"][dim]
        a_score = after["dimension_scores"][dim]
        dimension_deltas[dim] = {
            "before": b_score,
            "after": a_score,
            "delta": a_score - b_score
        }
        
    column_deltas = {}
    for col in before["columns"]:
        if col in after["columns"]:
            b_null = before["columns"][col]["null_count"]
            a_null = after["columns"][col]["null_count"]
            
            column_deltas[col] = {
                "null_count_before": b_null,
                "null_count_after": a_null,
                "null_reduction": b_null - a_null,
                "type_before": before["columns"][col]["inferred_type"],
                "type_after": after["columns"][col]["inferred_type"]
            }
            
            # If numeric, include min/max/mean comparison
            if before["columns"][col]["inferred_type"] == 'Numeric' and after["columns"][col]["inferred_type"] == 'Numeric':
                column_deltas[col].update({
                    "mean_before": before["columns"][col].get("mean"),
                    "mean_after": after["columns"][col].get("mean"),
                    "outliers_before": before["columns"][col].get("outliers_count", 0),
                    "outliers_after": after["columns"][col].get("outliers_count", 0)
                })
                
    return {
        "overall_before": before["overall_score"],
        "overall_after": after["overall_score"],
        "overall_delta": after["overall_score"] - before["overall_score"],
        "dimensions": dimension_deltas,
        "columns": column_deltas,
        "summary_before": before["summary"],
        "summary_after": after["summary"]
    }
