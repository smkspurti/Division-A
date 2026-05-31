# -*- coding: utf-8 -*-
"""
Transformation Verification Layer Unit Tests.
"""

import unittest
import pandas as pd
import numpy as np
from validation import TransformationVerifier

class TestTransformationVerifier(unittest.TestCase):
    
    def setUp(self):
        self.verifier = TransformationVerifier(row_loss_threshold=0.20, drift_alpha=0.01)
        self.df_before = pd.DataFrame({
            'ID': list(range(1, 16)),
            'Age': [20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0, 42.0, 44.0, 46.0, 48.0],
            'Salary': [50000.0, 52000.0, 54000.0, np.nan, 58000.0, 60000.0, np.nan, 64000.0, 66000.0, 68000.0, 70000.0, np.nan, 74000.0, 76000.0, 78000.0]
        })

    def test_schema_preserved(self):
        # Column added/dropped
        df_after = self.df_before.drop(columns=['Salary'])
        passed, msg = self.verifier.check_schema_preserved(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIn("Columns dropped", msg)

    def test_row_loss_under_limit(self):
        # Drop 1 row -> 1/15 = 6.67% loss -> Warning, but passes
        df_after = self.df_before.iloc[:-1]
        passed, msg = self.verifier.check_row_count_bounds(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIn("Data shrunk by 6.7%", msg)

    def test_row_loss_over_limit(self):
        # Drop 4 rows -> 4/15 = 26.67% loss -> Critical, fails
        df_after = self.df_before.iloc[:-4]
        passed, msg = self.verifier.check_row_count_bounds(self.df_before, df_after)
        self.assertFalse(passed)
        self.assertIn("Severe data loss: 26.7%", msg)

    def test_null_direction_positive(self):
        # Missingness decreases
        df_after = self.df_before.copy()
        df_after['Salary'] = df_after['Salary'].fillna(60000)
        passed, msg = self.verifier.check_null_direction(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIsNone(msg)

    def test_null_direction_negative(self):
        # Missingness increases
        df_after = self.df_before.copy()
        df_after.loc[0, 'Age'] = np.nan
        passed, msg = self.verifier.check_null_direction(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIn("Total missingness increased", msg)

    def test_new_nulls_warning(self):
        # Age was 100% complete, now has nulls
        df_after = self.df_before.copy()
        df_after.loc[0, 'Age'] = np.nan
        passed, msg = self.verifier.check_no_new_nulls(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIn("Complete columns now contain missing values: ['Age']", msg)

    def test_distribution_drift_detected(self):
        # Alter distribution of Age significantly
        df_after = self.df_before.copy()
        df_after['Age'] = [100.0] * 15
        passed, msg = self.verifier.check_distribution_drift(self.df_before, df_after)
        self.assertTrue(passed)
        self.assertIsNotNone(msg)
        self.assertIn("Significant statistical distribution drift", msg)

    def test_full_pipeline_success(self):
        # A normal imputation should pass fully
        df_after = self.df_before.copy()
        df_after['Salary'] = df_after['Salary'].fillna(df_after['Salary'].median())
        res = self.verifier.verify(self.df_before, df_after)
        
        self.assertTrue(res.passed)
        self.assertTrue(res.checks['row_loss_check'])
        self.assertEqual(len(res.warnings), 0)

    def test_full_pipeline_critical_failure(self):
        # Drop too many rows -> Verifier reports passed = False
        df_after = self.df_before.iloc[:-4]  # 40% loss
        res = self.verifier.verify(self.df_before, df_after)
        
        self.assertFalse(res.passed)
        self.assertFalse(res.checks['row_loss_check'])
        self.assertTrue(any("CRITICAL:" in w for w in res.warnings))

if __name__ == '__main__':
    unittest.main()
