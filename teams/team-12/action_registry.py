# -*- coding: utf-8 -*-
"""
Action Registry for DataCleanAgent.
Replaces arbitrary exec() commands with structured, auditable, and sandboxed actions.
Provides rollback snapshots, preconditions, and risk estimates.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Union
import pandas as pd
import numpy as np
import difflib

class ActionResult:
    """Contains the outcome of a cleaning action execution."""
    def __init__(
        self,
        success: bool,
        df: pd.DataFrame,
        rows_affected: int = 0,
        columns_affected: List[str] = None,
        description: str = "",
        error_message: Optional[str] = None
    ):
        self.success = success
        self.df = df
        self.rows_affected = rows_affected
        self.columns_affected = columns_affected or []
        self.description = description
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rows_affected": self.rows_affected,
            "columns_affected": self.columns_affected,
            "description": self.description,
            "error_message": self.error_message
        }


class CleaningAction(ABC):
    """Abstract base class for all registered cleaning actions."""
    
    @abstractmethod
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        """Verify if the action can run on this DataFrame with these parameters."""
        pass

    @abstractmethod
    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        """
        Executes the cleaning operation on a copy of the dataframe.
        Returns: (modified_df, rows_affected, columns_affected, description)
        """
        pass

    @abstractmethod
    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        """Estimates the execution risk: 'Low', 'Medium', or 'High'."""
        pass


# ============================================================
# Core Action Implementations
# ============================================================

class MedianImputer(CleaningAction):
    """Imputes missing values in a numeric column with its median."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found in dataset."
        if not pd.api.types.is_numeric_dtype(df[column]):
            return False, f"Column '{column}' is not numeric. Cannot impute with median."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        df_new = df.copy()
        
        # Detect initial null count
        null_mask = df_new[column].isna()
        rows_affected = null_mask.sum()
        
        if rows_affected > 0:
            median_val = df_new[column].median()
            df_new[column] = df_new[column].fillna(median_val)
            desc = f"Imputed {rows_affected} missing values in '{column}' using the median value of {median_val:.4g}."
        else:
            desc = f"No missing values found in numeric column '{column}'. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class GroupedMedianImputer(CleaningAction):
    """Imputes missing values in a numeric column using medians grouped by other columns."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        group_cols = kwargs.get("group_cols")
        
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found in dataset."
        if not pd.api.types.is_numeric_dtype(df[column]):
            return False, f"Column '{column}' is not numeric."
            
        if not group_cols:
            return False, "Parameter 'group_cols' (list of grouping columns) is required."
            
        if isinstance(group_cols, str):
            group_cols = [group_cols]
            
        for gcol in group_cols:
            if gcol not in df.columns:
                return False, f"Grouping column '{gcol}' not found in dataset."
                
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        group_cols = kwargs.get("group_cols")
        if isinstance(group_cols, str):
            group_cols = [group_cols]
            
        df_new = df.copy()
        null_mask = df_new[column].isna()
        rows_affected = null_mask.sum()
        
        if rows_affected > 0:
            # Calculate grouped medians
            # Fallback to global median for groups that don't have median (e.g., all NaN in group)
            global_median = df_new[column].median()
            grouped_medians = df_new.groupby(group_cols)[column].transform("median")
            grouped_medians = grouped_medians.fillna(global_median)
            
            df_new[column] = df_new[column].fillna(grouped_medians)
            desc = f"Imputed {rows_affected} missing values in '{column}' using grouped medians by {group_cols}."
        else:
            desc = f"No missing values found in '{column}'. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class ModeImputer(CleaningAction):
    """Imputes missing values in a categorical column with its mode."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found in dataset."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        df_new = df.copy()
        
        null_mask = df_new[column].isna()
        rows_affected = null_mask.sum()
        
        if rows_affected > 0:
            modes = df_new[column].mode()
            if not modes.empty:
                mode_val = modes.iloc[0]
                df_new[column] = df_new[column].fillna(mode_val)
                desc = f"Imputed {rows_affected} missing values in '{column}' using the mode: '{mode_val}'."
            else:
                desc = f"Could not determine mode for '{column}' (all values might be null). No changes made."
                rows_affected = 0
        else:
            desc = f"No missing values found in column '{column}'. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class ColumnDropper(CleaningAction):
    """Drops a list of columns or columns with null percentage above a threshold."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        columns = kwargs.get("columns")
        threshold = kwargs.get("threshold")
        
        if not columns and threshold is None:
            return False, "Either 'columns' (list) or 'threshold' (float null pct 0.0 - 1.0) must be provided."
            
        if columns:
            if isinstance(columns, str):
                columns = [columns]
            for col in columns:
                if col not in df.columns:
                    return False, f"Column '{col}' not found in dataset."
                    
        if threshold is not None:
            if not (0.0 <= threshold <= 1.0):
                return False, "Threshold must be between 0.0 and 1.0."
                
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        columns = kwargs.get("columns", [])
        if isinstance(columns, str):
            columns = [columns]
        threshold = kwargs.get("threshold")
        
        df_new = df.copy()
        dropped_cols = []
        
        if threshold is not None:
            null_pcts = df_new.isna().mean()
            cols_above_thresh = null_pcts[null_pcts > threshold].index.tolist()
            dropped_cols.extend(cols_above_thresh)
            
        for col in columns:
            if col not in dropped_cols:
                dropped_cols.append(col)
                
        # Drop columns
        df_new = df_new.drop(columns=dropped_cols)
        desc = f"Dropped columns: {dropped_cols}."
        if threshold is not None:
            desc += f" (Threshold of {threshold*100:.1f}% missingness exceeded)"
            
        return df_new, len(df_new), dropped_cols, desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        # High risk as it deletes data columns
        return "High"


class DuplicateRemover(CleaningAction):
    """Removes exact duplicate rows from the dataset, optionally ignoring index/IDs."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        subset = kwargs.get("subset")
        keep = kwargs.get("keep", "first")
        
        df_new = df.copy()
        
        # If subset is provided, validate columns
        valid_subset = None
        if subset:
            if isinstance(subset, str):
                subset = [subset]
            valid_subset = [c for c in subset if c in df_new.columns]
            
        initial_rows = len(df_new)
        df_new = df_new.drop_duplicates(subset=valid_subset, keep=keep)
        rows_affected = initial_rows - len(df_new)
        
        if rows_affected > 0:
            desc = f"Removed {rows_affected} exact duplicate records."
            if valid_subset:
                desc += f" (analyzed subset: {valid_subset})"
        else:
            desc = "No duplicate rows found. No changes made."
            
        return df_new, int(rows_affected), list(df_new.columns), desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Medium"


class CategoryNormalizer(CleaningAction):
    """Normalizes categorical entries using fuzzy matching to standard labels."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        custom_mapping = kwargs.get("mapping") # optional dictionary mapping old -> new
        
        df_new = df.copy()
        # Coerce column to string to process categories safely
        series = df_new[column].astype(str).str.strip()
        # Handle nan values that became 'nan' string
        series[df_new[column].isna()] = np.nan
        
        rows_affected = 0
        desc_details = []
        
        if custom_mapping:
            # Apply explicit mapping
            mask = series.isin(custom_mapping.keys())
            rows_affected = mask.sum()
            df_new[column] = df_new[column].map(lambda x: custom_mapping.get(str(x).strip(), x))
            desc = f"Standardized values in '{column}' using custom mapping: {custom_mapping}."
        else:
            # Auto-fuzzy group mapping
            unique_vals = series.dropna().unique().tolist()
            mapping = {}
            visited = set()
            
            # Sort by frequency descending so common names become targets
            val_counts = series.value_counts()
            sorted_vals = val_counts.index.tolist()
            
            # Group by case-insensitive normalized form to resolve casing first
            casing_groups = {}
            for val in sorted_vals:
                norm = val.lower()
                if norm not in casing_groups:
                    casing_groups[norm] = []
                casing_groups[norm].append(val)
                
            # For each case-insensitive group, map all members to the dominant casing
            for norm, members in casing_groups.items():
                dominant = members[0] # first has highest frequency
                for m in members:
                    if m != dominant:
                        mapping[m] = dominant
                        
            # Now run fuzzy matching among the dominant case-insensitive forms
            dominant_vals = [members[0] for members in casing_groups.values()]
            for val in dominant_vals:
                val_norm = val.lower()
                if val_norm in visited:
                    continue
                # Find close matches among other dominant values (lowercased)
                other_norms = [v.lower() for v in dominant_vals if v.lower() not in visited]
                matches = difflib.get_close_matches(val_norm, other_norms, n=10, cutoff=0.82)
                for match_norm in matches:
                    if match_norm not in visited:
                        # Find the corresponding raw dominant value
                        match_val = next(v for v in dominant_vals if v.lower() == match_norm)
                        mapping[match_val] = val
                        visited.add(match_norm)
                        
            # Apply auto-mapping
            changes = {}
            for original, normalized in mapping.items():
                if original != normalized:
                    mask = series == original
                    cnt = mask.sum()
                    if cnt > 0:
                        rows_affected += cnt
                        changes[original] = normalized
                        df_new.loc[df_new[column].astype(str).str.strip() == original, column] = normalized
                        
            if rows_affected > 0:
                desc = f"Standardized {rows_affected} text variants in '{column}' using fuzzy matching: {changes}."
            else:
                desc = f"No text variations detected in '{column}'. No changes made."
                
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Medium"


class IQRClamper(CleaningAction):
    """Clamps numeric outliers in a column using Interquartile Range (IQR) bounds."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        if not pd.api.types.is_numeric_dtype(df[column]):
            return False, f"Column '{column}' is not numeric."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        multiplier = kwargs.get("multiplier", 1.5)
        
        df_new = df.copy()
        series = df_new[column]
        
        # Calculate IQR
        q25 = series.quantile(0.25)
        q75 = series.quantile(0.75)
        iqr = q75 - q25
        lower_bound = q25 - multiplier * iqr
        upper_bound = q75 + multiplier * iqr
        
        # Check outliers
        under_mask = series < lower_bound
        over_mask = series > upper_bound
        rows_affected = under_mask.sum() + over_mask.sum()
        
        if rows_affected > 0:
            df_new[column] = series.clip(lower=lower_bound, upper=upper_bound)
            desc = (f"Clamped {rows_affected} outliers in '{column}' to IQR bounds "
                    f"[{lower_bound:.4g}, {upper_bound:.4g}] using multiplier={multiplier}.")
        else:
            desc = f"No numeric outliers found in '{column}' outside IQR bounds. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Medium"


class NumericCoercer(CleaningAction):
    """Coerces a column to numeric, replacing unparseable characters with NaN or default."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        df_new = df.copy()
        
        # Remove common currency/commas symbol string formatting
        original_series = df_new[column].astype(str)
        cleaned_series = (original_series
                          .str.replace('$', '', regex=False)
                          .str.replace(',', '', regex=False)
                          .str.replace(' ', '', regex=False)
                          .str.strip())
        
        # Map known placeholder patterns back to nan
        sentinel_nulls = ['?', 'n/a', 'nan', 'null', 'none', 'unknown', '-']
        cleaned_series[cleaned_series.str.lower().isin(sentinel_nulls)] = np.nan
        cleaned_series[original_series.isna()] = np.nan
        
        # Coerce to numeric
        coerced = pd.to_numeric(cleaned_series, errors='coerce')
        
        # Count parsing failures that introduced new NaNs
        new_nans = coerced.isna() & df_new[column].notna()
        rows_affected = new_nans.sum()
        
        # Apply transformation
        df_new[column] = coerced
        
        if rows_affected > 0:
            desc = f"Coerced '{column}' to numeric type. Replaced {rows_affected} unparseable values with NaN."
        else:
            desc = f"Coerced '{column}' to numeric successfully without introducing new missing values."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class BooleanCoercer(CleaningAction):
    """Coerces columns to standard boolean representations (0 or 1)."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        df_new = df.copy()
        
        series_str = df_new[column].astype(str).str.strip().str.lower()
        series_str[df_new[column].isna()] = "nan"
        
        true_vals = ["1", "1.0", "true", "yes", "y", "t"]
        false_vals = ["0", "0.0", "false", "no", "n", "f"]
        
        def map_bool(val):
            if val in true_vals:
                return 1
            elif val in false_vals:
                return 0
            else:
                return np.nan
                
        mapped = series_str.map(map_bool)
        
        # Calculate rows modified
        rows_affected = (df_new[column] != mapped).sum()
        df_new[column] = mapped
        
        desc = f"Coerced boolean column '{column}' to standard integers [0, 1]. Normalized {rows_affected} cells."
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class ConstantColumnDropper(CleaningAction):
    """Drops columns that contain only a single unique value (zero variance)."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        df_new = df.copy()
        
        constant_cols = []
        for col in df_new.columns:
            # Dropna=True by default, we want to know if there is only 1 non-null value
            unique_count = df_new[col].nunique(dropna=True)
            if unique_count <= 1:
                constant_cols.append(col)
                
        if constant_cols:
            df_new = df_new.drop(columns=constant_cols)
            desc = f"Dropped constant/zero-variance columns: {constant_cols}."
        else:
            desc = "No constant columns (with zero variance) detected. No changes made."
            
        return df_new, len(df_new), constant_cols, desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class NegativeValueClamper(CleaningAction):
    """Clamps negative values in a numeric column to 0 (useful for counts, fares, age, etc.)."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        if not pd.api.types.is_numeric_dtype(df[column]):
            return False, f"Column '{column}' is not numeric."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        df_new = df.copy()
        
        negative_mask = df_new[column] < 0
        rows_affected = negative_mask.sum()
        
        if rows_affected > 0:
            df_new.loc[negative_mask, column] = 0.0
            desc = f"Clamped {rows_affected} negative values in '{column}' to 0.0."
        else:
            desc = f"No negative values detected in numeric column '{column}'. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class PlaceholderFiller(CleaningAction):
    """Fills remaining null values in a column with a specific static placeholder."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        placeholder = kwargs.get("placeholder")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        if placeholder is None:
            return False, "Parameter 'placeholder' is required."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        placeholder = kwargs.get("placeholder")
        
        df_new = df.copy()
        null_mask = df_new[column].isna()
        rows_affected = null_mask.sum()
        
        if rows_affected > 0:
            df_new[column] = df_new[column].fillna(placeholder)
            desc = f"Filled {rows_affected} remaining missing values in '{column}' with placeholder value '{placeholder}'."
        else:
            desc = f"No missing values found in '{column}'. No changes made."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


class InvalidValueReplacer(CleaningAction):
    """Replaces invalid/out-of-range values in a column with NaN or a fallback value."""
    
    def validate_preconditions(self, df: pd.DataFrame, **kwargs) -> Tuple[bool, Optional[str]]:
        column = kwargs.get("column")
        if not column:
            return False, "Parameter 'column' is required."
        if column not in df.columns:
            return False, f"Column '{column}' not found."
        return True, None

    def execute(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, int, List[str], str]:
        column = kwargs.get("column")
        allowed_values = kwargs.get("allowed_values")
        min_val = kwargs.get("min_val")
        max_val = kwargs.get("max_val")
        replace_with = kwargs.get("replace_with", np.nan)
        
        df_new = df.copy()
        
        # Determine invalid mask
        mask = pd.Series(False, index=df_new.index)
        
        # If we have allowed values
        if allowed_values is not None:
            # Check values that are not null and not in allowed values
            # Need to coerce types safely for comparison
            series_str = df_new[column].dropna().astype(str).str.strip().str.replace('.0', '', regex=False)
            allowed_str = [str(v) for v in allowed_values]
            invalid_indices = series_str[~series_str.isin(allowed_str)].index
            mask.loc[invalid_indices] = True
            
        # If we have numeric range bounds
        if min_val is not None or max_val is not None:
            # Coerce column to numeric for comparison
            numeric_series = pd.to_numeric(df_new[column], errors='coerce')
            if min_val is not None:
                mask = mask | (numeric_series < min_val)
            if max_val is not None:
                mask = mask | (numeric_series > max_val)
                
        # Count rows affected (only replace if not already null or if changing value)
        rows_affected = (mask & df_new[column].notna()).sum()
        
        if rows_affected > 0:
            df_new.loc[mask, column] = replace_with
            desc = f"Replaced {rows_affected} invalid entries in '{column}' with {replace_with}."
            if allowed_values:
                desc += f" (Values not in allowed set: {allowed_values})"
            if min_val is not None or max_val is not None:
                desc += f" (Values outside bounds: [{min_val}, {max_val}])"
        else:
            desc = f"No invalid values detected in '{column}' based on the specified limits."
            
        return df_new, int(rows_affected), [column], desc

    def estimate_risk(self, df: pd.DataFrame, **kwargs) -> str:
        return "Low"


# ============================================================
# Action Registry Mapping
# ============================================================

ACTION_REGISTRY: Dict[str, CleaningAction] = {
    "median_imputation": MedianImputer(),
    "grouped_median_imputation": GroupedMedianImputer(),
    "mode_imputation": ModeImputer(),
    "drop_columns": ColumnDropper(),
    "remove_duplicates": DuplicateRemover(),
    "normalize_categories": CategoryNormalizer(),
    "clamp_iqr_outliers": IQRClamper(),
    "coerce_numeric": NumericCoercer(),
    "coerce_boolean": BooleanCoercer(),
    "drop_constant_columns": ConstantColumnDropper(),
    "clamp_negative_values": NegativeValueClamper(),
    "fill_placeholders": PlaceholderFiller(),
    "replace_invalid_values": InvalidValueReplacer()
}

def get_action_python_code(action_name: str, **kwargs) -> str:
    """Generates the equivalent pandas Python code representation for audit/log logging."""
    if action_name == "median_imputation":
        col = kwargs.get("column", "column")
        return f"df['{col}'] = df['{col}'].fillna(df['{col}'].median())"
    elif action_name == "grouped_median_imputation":
        col = kwargs.get("column", "column")
        grp = kwargs.get("group_cols", ["group_col"])
        return f"df['{col}'] = df['{col}'].fillna(df.groupby({grp})['{col}'].transform('median'))"
    elif action_name == "mode_imputation":
        col = kwargs.get("column", "column")
        return f"df['{col}'] = df['{col}'].fillna(df['{col}'].mode()[0] if not df['{col}'].mode().empty else 'Unknown')"
    elif action_name == "drop_columns":
        cols = kwargs.get("columns", [])
        thresh = kwargs.get("threshold")
        if thresh is not None:
            return f"# Drop columns with missingness > {thresh*100}%\nnull_pcts = df.isna().mean()\ncols_to_drop = null_pcts[null_pcts > {thresh}].index.tolist()\ndf.drop(columns=cols_to_drop, inplace=True)"
        else:
            return f"df.drop(columns={cols}, inplace=True)"
    elif action_name == "remove_duplicates":
        subset = kwargs.get("subset")
        keep = kwargs.get("keep", "first")
        sub_str = f"subset={subset}, " if subset else ""
        return f"df.drop_duplicates({sub_str}keep='{keep}', inplace=True)"
    elif action_name == "normalize_categories":
        col = kwargs.get("column", "column")
        mapping = kwargs.get("mapping")
        if mapping:
            return f"df['{col}'] = df['{col}'].astype(str).str.strip().replace({mapping})"
        else:
            return f"# Auto-fuzzy match and normalize categories in '{col}'\n# Implemented via difflib standard library"
    elif action_name == "clamp_iqr_outliers":
        col = kwargs.get("column", "column")
        mult = kwargs.get("multiplier", 1.5)
        return (f"q25 = df['{col}'].quantile(0.25)\n"
                f"q75 = df['{col}'].quantile(0.75)\n"
                f"iqr = q75 - q25\n"
                f"df['{col}'] = df['{col}'].clip(lower=q25 - {mult}*iqr, upper=q75 + {mult}*iqr)")
    elif action_name == "coerce_numeric":
        col = kwargs.get("column", "column")
        return (f"df['{col}'] = df['{col}'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()\n"
                f"df['{col}'] = pd.to_numeric(df['{col}'], errors='coerce')")
    elif action_name == "coerce_boolean":
        col = kwargs.get("column", "column")
        return (f"# Coerce column '{col}' values (yes/no/true/false) to [0, 1]\n"
                f"true_vals = ['1', 'true', 'yes', 'y', 't']\n"
                f"false_vals = ['0', 'false', 'no', 'n', 'f']\n"
                f"df['{col}'] = df['{col}'].astype(str).str.strip().str.lower().map(lambda x: 1 if x in true_vals else (0 if x in false_vals else np.nan))")
    elif action_name == "drop_constant_columns":
        return "# Drop constant (zero variance) columns\nconstant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]\ndf.drop(columns=constant_cols, inplace=True)"
    elif action_name == "clamp_negative_values":
        col = kwargs.get("column", "column")
        return f"df.loc[df['{col}'] < 0, '{col}'] = 0.0"
    elif action_name == "fill_placeholders":
        col = kwargs.get("column", "column")
        ph = kwargs.get("placeholder", "Unknown")
        return f"df['{col}'] = df['{col}'].fillna('{ph}')"
    elif action_name == "replace_invalid_values":
        col = kwargs.get("column", "column")
        allowed = kwargs.get("allowed_values")
        min_v = kwargs.get("min_val")
        max_v = kwargs.get("max_val")
        rep = kwargs.get("replace_with", "np.nan")
        rep_val = "np.nan" if rep is None or (isinstance(rep, float) and np.isnan(rep)) else repr(rep)
        
        lines = []
        if allowed:
            lines.append(f"allowed_str = [str(x) for x in {allowed}]")
            lines.append(f"invalid_mask = ~df['{col}'].astype(str).str.strip().str.replace('.0', '', regex=False).isin(allowed_str) & df['{col}'].notna()")
            lines.append(f"df.loc[invalid_mask, '{col}'] = {rep_val}")
        if min_v is not None or max_v is not None:
            num_expr = f"pd.to_numeric(df['{col}'], errors='coerce')"
            conds = []
            if min_v is not None:
                conds.append(f"({num_expr} < {min_v})")
            if max_v is not None:
                conds.append(f"({num_expr} > {max_v})")
            cond_expr = " | ".join(conds)
            lines.append(f"df.loc[{cond_expr}, '{col}'] = {rep_val}")
        return "\n".join(lines) if lines else f"# No invalid values limits specified for '{col}'"
    return f"# Custom Action: {action_name}"


def execute_action(action_name: str, df: pd.DataFrame, **kwargs) -> ActionResult:
    """
    Looks up, validates, and runs an action against a DataFrame.
    Captures any execution errors, guaranteeing the app never crashes.
    """
    if action_name not in ACTION_REGISTRY:
        return ActionResult(
            success=False,
            df=df,
            error_message=f"Action '{action_name}' is not registered in the Action Registry."
        )
        
    action = ACTION_REGISTRY[action_name]
    
    # 1. Precondition check
    is_valid, err_msg = action.validate_preconditions(df, **kwargs)
    if not is_valid:
        return ActionResult(
            success=False,
            df=df,
            error_message=f"Precondition validation failed: {err_msg}"
        )
        
    # 2. Execution in a try-except sandbox
    try:
        modified_df, rows_affected, cols_affected, description = action.execute(df, **kwargs)
        return ActionResult(
            success=True,
            df=modified_df,
            rows_affected=rows_affected,
            columns_affected=cols_affected,
            description=description
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return ActionResult(
            success=False,
            df=df,
            error_message=f"Unexpected error executing '{action_name}': {str(e)}",
            description=f"Action execution crashed with error: {str(e)}.\nTraceback:\n{tb}"
        )
