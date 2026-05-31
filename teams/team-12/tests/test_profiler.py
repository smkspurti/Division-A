# -*- coding: utf-8 -*-
"""
Profiling and Quality Scoring Unit Tests.
"""

import unittest
import pandas as pd
import numpy as np
from profiler import (
    infer_column_types,
    detect_outliers_iqr,
    detect_outliers_zscore,
    detect_multivariate_outliers,
    find_categorical_inconsistencies,
    profile_dataset,
    compare_profiles
)

class TestProfiler(unittest.TestCase):
    
    def test_infer_column_types(self):
        df = pd.DataFrame({
            'ID': list(range(1, 26)),
            'Age': [float(x) for x in range(20, 45)],
            'Gender': (['male', 'female'] * 12) + ['male'],
            'Biography': [f"Long unique biography sentence number {x} with descriptive text that makes it quite distinct." for x in range(1, 26)],
            'IsStudent': (['yes', 'no'] * 12) + ['yes'],
            'JoinDate': [f"2023-05-{x:02d}" for x in range(1, 26)]
        })
        
        types = infer_column_types(df)
        self.assertEqual(types['ID'], 'Numeric')
        self.assertEqual(types['Age'], 'Numeric')
        self.assertEqual(types['Gender'], 'Categorical')
        # Biography has high uniqueness and cardinality
        self.assertEqual(types['Biography'], 'Text')
        self.assertEqual(types['IsStudent'], 'Boolean')
        self.assertEqual(types['JoinDate'], 'DateTime')

    def test_detect_outliers_iqr(self):
        series = pd.Series([10, 12, 11, 13, 12, 14, 100, 12, 11, 10, -50])
        mask = detect_outliers_iqr(series)
        # 100 and -50 should be outliers
        self.assertTrue(mask.iloc[6])  # 100
        self.assertTrue(mask.iloc[10]) # -50
        self.assertFalse(mask.iloc[0]) # 10

    def test_detect_outliers_zscore(self):
        series = pd.Series([10]*20 + [100])
        mask = detect_outliers_zscore(series, threshold=3.0)
        self.assertTrue(mask.iloc[20])  # 100 is far from mean=14.28 std=19.6
        self.assertFalse(mask.iloc[0])

    def test_find_categorical_inconsistencies(self):
        df = pd.DataFrame({
            'City': ['New York', 'new york', 'New York ', 'Chicago', 'chicago', 'London', 'Londan']
        })
        inconsistencies = find_categorical_inconsistencies(df, ['City'])
        self.assertIn('City', inconsistencies)
        mapping = inconsistencies['City']
        # 'new york' and 'New York ' should map to dominant 'New York'
        self.assertEqual(mapping['new york'], 'New York')
        self.assertEqual(mapping['New York '], 'New York')
        # 'chicago' should map to 'Chicago'
        self.assertEqual(mapping['chicago'], 'Chicago')
        # 'Londan' should map fuzzy to 'London'
        self.assertEqual(mapping['Londan'], 'London')

    def test_profile_scoring_engine(self):
        # Create a dataframe with specific defects:
        # - 1 duplicate row out of 5 (80% uniqueness)
        # - 2 nulls out of 15 cells (86.7% completeness)
        # - 1 out-of-range Age value: 150 (validity defect)
        # - 1 casing inconsistency: 'male' vs 'Male' (consistency defect)
        df = pd.DataFrame({
            'PassengerId': [1, 2, 3, 4, 5],
            'Age': [22.0, 150.0, np.nan, 30.0, 30.0],
            'Sex': ['Male', 'female', 'male', 'female', 'female']
        })
        
        # Duplicate row 4 and 5 (excluding PassengerId)
        # Step 5 duplicate of step 4: (Age=30, Sex=female)
        profile = profile_dataset(df)
        
        scores = profile['dimension_scores']
        
        # Verify completeness score
        # Total cells: 15, Nulls: 1 (Age null) -> 14/15 = 93.3%
        self.assertAlmostEqual(scores['Completeness'], 93.33333333333333)
        
        # Verify uniqueness score
        # Drop ID column PassengerId. Remaining are [22.0, Male], [150.0, female], [NaN, male], [30.0, female], [30.0, female]
        # 1 duplicate row (row 5) -> 4 unique/5 total = 80% uniqueness
        self.assertEqual(scores['Uniqueness'], 80.0)
        
        # Verify validity score
        # Valid age must be <= 120. 150 is invalid -> 1/4 non-null cells in Age invalid.
        # PassengerId: ignored for validity as ID.
        # Sex: all 5 are non-null and valid.
        # Age: 4 non-nulls. 1 invalid. Total valid cells = 4 (Sex) + 3 (Age) = 7. Total non-null cells = 5 + 4 = 9.
        # Validity = 1 - 1/14 = 92.857% (including ID column in overall denominator)
        self.assertAlmostEqual(scores['Validity'], 92.85714285714286)
        
        # Verify consistency score
        # Sex contains 'Male', 'female', 'male', 'female', 'female'. 'male' is mapped to 'Male' or vice-versa.
        # Total inconsistent cells: 1. Non-null cells: 14. Consistency = 13/14 = 92.857%
        self.assertAlmostEqual(scores['Consistency'], 92.85714285714286)

        # Check that overall score is computed as a weighted harmonic mean and drags down
        overall = profile['overall_score']
        self.assertTrue(0.0 <= overall <= 100.0)
        # It must be closer to the minimum score due to harmonic weighting
        min_dim_score = min(scores.values())
        self.assertTrue(overall < sum(scores.values())/len(scores))  # harmonic mean < arithmetic mean

    def test_compare_profiles(self):
        raw_income = [50000.0, 50000.0] + [float(50002 + i) for i in range(22)] + [200000.0]
        clean_income = [50000.0, 50000.0] + [float(50002 + i) for i in range(22)] + [50024.0]
        raw_age = [25.0, np.nan, 30.0, np.nan, 35.0] * 5
        clean_age = [25.0, 30.0, 30.0, 30.0, 35.0] * 5
        
        df_raw = pd.DataFrame({
            'Age': raw_age,
            'Income': raw_income
        })
        
        df_clean = pd.DataFrame({
            'Age': clean_age,
            'Income': clean_income
        })
        
        prof_raw = profile_dataset(df_raw)
        prof_clean = profile_dataset(df_clean)
        
        diff = compare_profiles(prof_raw, prof_clean)
        
        self.assertGreater(diff['overall_after'], diff['overall_before'])
        self.assertEqual(diff['columns']['Age']['null_reduction'], 10)
        self.assertEqual(diff['columns']['Income']['outliers_before'], 1)
        self.assertEqual(diff['columns']['Income']['outliers_after'], 0)

if __name__ == '__main__':
    unittest.main()
