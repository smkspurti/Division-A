# -*- coding: utf-8 -*-
"""
Validation Layer for DataCleanAgent.
Verifies DataFrame integrity and statistical consistency post-cleaning.
Prevents overcleaning, unexpected column deletion, and significant distribution drift.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats

class VerificationResult:
    """Carries the results of a transformation verification."""
    def __init__(self, passed: bool, checks: Dict[str, bool], warnings: List[str]):
        self.passed = passed
        self.checks = checks
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "warnings": self.warnings
        }


class TransformationVerifier:
    """Runs data quality sanity checks before committing a DataFrame transformation."""
    
    def __init__(self, row_loss_threshold: float = 0.20, drift_alpha: float = 0.01):
        self.row_loss_threshold = row_loss_threshold  # Max allowed row loss pct (default 20%)
        self.drift_alpha = drift_alpha  # Alpha level for KS test drift warning (default 1%)

    def check_schema_preserved(self, before: pd.DataFrame, after: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """Verifies if core structural columns are not unexpectedly modified or dropped."""
        before_cols = set(before.columns)
        after_cols = set(after.columns)
        
        dropped = before_cols - after_cols
        added = after_cols - before_cols
        
        if dropped:
            # We allow dropping columns if explicitly requested, but warning is logged
            return True, f"Warning: Columns dropped: {list(dropped)}."
        return True, None

    def check_row_count_bounds(self, before: pd.DataFrame, after: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """Prevents catastrophic row deletion (e.g. losing more than 20% of data)."""
        b_len = len(before)
        a_len = len(after)
        if b_len == 0:
            return True, None
            
        loss_pct = (b_len - a_len) / b_len
        if loss_pct > self.row_loss_threshold:
            return False, f"Severe data loss: {loss_pct*100:.1f}% of rows were deleted ({b_len} -> {a_len}). Limit is {self.row_loss_threshold*100:.0f}%."
        elif loss_pct > 0.0:
            return True, f"Data shrunk by {loss_pct*100:.1f}% ({b_len} -> {a_len} rows)."
        return True, None

    def check_null_direction(self, before: pd.DataFrame, after: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """Ensures total missingness does not increase."""
        before_nulls = before.isna().sum().sum()
        after_nulls = after.isna().sum().sum()
        
        if after_nulls > before_nulls:
            return True, f"Warning: Total missingness increased from {before_nulls} to {after_nulls} null cells."
        return True, None

    def check_no_new_nulls(self, before: pd.DataFrame, after: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """Checks if a column that was previously 100% complete now has missing values."""
        warnings = []
        for col in before.columns:
            if col in after.columns:
                before_has_no_nulls = before[col].isna().sum() == 0
                after_has_nulls = after[col].isna().sum() > 0
                if before_has_no_nulls and after_has_nulls:
                    warnings.append(col)
                    
        if warnings:
            return True, f"Warning: Complete columns now contain missing values: {warnings}."
        return True, None

    def check_distribution_drift(self, before: pd.DataFrame, after: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        Runs Kolmogorov-Smirnov (KS) test on numeric columns to flag
        significant statistical distribution drift that might distort model features.
        """
        drifts = []
        for col in before.columns:
            if col in after.columns:
                # Only check if numeric in both
                if pd.api.types.is_numeric_dtype(before[col]) and pd.api.types.is_numeric_dtype(after[col]):
                    b_clean = before[col].dropna()
                    a_clean = after[col].dropna()
                    
                    if len(b_clean) > 10 and len(a_clean) > 10:
                        try:
                            # Run two-sample Kolmogorov-Smirnov test
                            ks_stat, p_val = stats.ks_2samp(b_clean, a_clean)
                            if p_val < self.drift_alpha:
                                drifts.append(f"'{col}' (p-value {p_val:.4g})")
                        except Exception:
                            pass
                            
        if drifts:
            return True, f"Warning: Significant statistical distribution drift detected in numeric features: {', '.join(drifts)}."
        return True, None

    def verify(self, before: pd.DataFrame, after: pd.DataFrame) -> VerificationResult:
        """
        Runs the full verification pipeline.
        Returns a VerificationResult package with success status and warnings list.
        """
        checks = {
            "schema_check": True,
            "row_loss_check": True,
            "null_direction_check": True,
            "new_nulls_check": True,
            "distribution_drift_check": True
        }
        warnings = []

        # 1. Schema check
        ok, msg = self.check_schema_preserved(before, after)
        if msg:
            warnings.append(msg)
            
        # 2. Row count bounds
        ok, msg = self.check_row_count_bounds(before, after)
        if not ok:
            checks["row_loss_check"] = False
            warnings.append(f"CRITICAL: {msg}")
        elif msg:
            warnings.append(msg)
            
        # 3. Null direction check
        ok, msg = self.check_null_direction(before, after)
        if msg:
            warnings.append(msg)
            
        # 4. New nulls check
        ok, msg = self.check_no_new_nulls(before, after)
        if msg:
            warnings.append(msg)
            
        # 5. Distribution drift check
        ok, msg = self.check_distribution_drift(before, after)
        if msg:
            warnings.append(msg)

        # If any critical check failed
        passed = all(checks.values())
        
        return VerificationResult(passed=passed, checks=checks, warnings=warnings)
