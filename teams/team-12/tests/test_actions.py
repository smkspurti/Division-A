# -*- coding: utf-8 -*-
"""
Action Registry and Sandboxed Cleaning Tasks Unit Tests.
"""

import unittest
import pandas as pd
import numpy as np
from action_registry import (
    execute_action,
    get_action_python_code,
    ACTION_REGISTRY
)

class TestActionRegistry(unittest.TestCase):
    
    def setUp(self):
        self.df = pd.DataFrame({
            'ID': [1, 2, 3, 4, 5, 6, 7, 8],
            'Age': [20.0, np.nan, 30.0, 40.0, np.nan, 30.0, 25.0, 35.0],
            'Fare': [10.0, 500.0, 15.0, -5.0, 20.0, 10.0, 15.0, 20.0],  # Outlier and negative value
            'Sex': ['male', 'Female', 'MALE', 'female', 'male', 'female', 'male', 'male'],
            'Survived': [1, 0, 1, 0, 1, 0, 1, 0],
            'HasPass': ['yes', 'no', 'YES', 'NO', np.nan, 'yes', 'no', 'yes'],
            'Constant': ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A']
        })

    def test_median_imputer(self):
        res = execute_action("median_imputation", self.df, column="Age")
        self.assertTrue(res.success)
        self.assertEqual(res.rows_affected, 2)
        # Median of 20, 30, 40, 30, 25, 35 is 30
        self.assertEqual(res.df.loc[1, 'Age'], 30.0)
        self.assertEqual(res.df.loc[4, 'Age'], 30.0)

    def test_median_imputer_preconditions(self):
        # Missing column
        res = execute_action("median_imputation", self.df, column="NonExistent")
        self.assertFalse(res.success)
        self.assertIn("not found", res.error_message.lower())

        # Non-numeric column
        res = execute_action("median_imputation", self.df, column="Sex")
        self.assertFalse(res.success)
        self.assertIn("not numeric", res.error_message.lower())

    def test_grouped_median_imputer(self):
        # We group Age by Survived. 
        # Survived=1 has Age=[20, 30, NaN, 25] -> Non-nulls: [20, 25, 30] -> Median is 25.
        # Survived=0 has Age=[NaN, 40, 30, 35] -> Non-nulls: [30, 35, 40] -> Median is 35.
        res = execute_action("grouped_median_imputation", self.df, column="Age", group_cols=["Survived"])
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[1, 'Age'], 35.0) # Survived=0 row
        self.assertEqual(res.df.loc[4, 'Age'], 25.0) # Survived=1 row

    def test_mode_imputer(self):
        # Sex mode is 'male'
        res = execute_action("mode_imputation", self.df, column="Sex")
        self.assertTrue(res.success)
        # We inject a null in Sex
        df_null = self.df.copy()
        df_null.loc[4, 'Sex'] = np.nan
        res = execute_action("mode_imputation", df_null, column="Sex")
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[4, 'Sex'], 'male')

    def test_column_dropper(self):
        res = execute_action("drop_columns", self.df, columns=["Constant", "HasPass"])
        self.assertTrue(res.success)
        self.assertNotIn("Constant", res.df.columns)
        self.assertNotIn("HasPass", res.df.columns)

    def test_duplicate_remover(self):
        # Create duplicate row
        df_dup = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        res = execute_action("remove_duplicates", df_dup)
        self.assertTrue(res.success)
        self.assertEqual(len(res.df), 8)

    def test_category_normalizer(self):
        # Sex has ['male', 'Female', 'MALE', 'female', 'male']
        # Normalized form should group casing variations to dominant form ('male')
        res = execute_action("normalize_categories", self.df, column="Sex")
        self.assertTrue(res.success)
        unique_sex = res.df['Sex'].unique()
        self.assertIn('male', unique_sex)
        self.assertIn('female', unique_sex)
        self.assertEqual(len(unique_sex), 2)

    def test_iqr_clamper(self):
        # Outlier is 500.0. Q1=10, Q3=20, IQR=10. Bounds: [10 - 15, 20 + 15] = [-5, 35].
        # 500 should be clipped to 35.0
        res = execute_action("clamp_iqr_outliers", self.df, column="Fare", multiplier=1.5)
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[1, 'Fare'], 35.0)
        # Negative outlier -5.0 remains since lower bound is -5.0
        self.assertEqual(res.df.loc[3, 'Fare'], -5.0)

    def test_coerce_numeric(self):
        df_str = pd.DataFrame({'Price': ['$1,200.50', ' $350 ', 'N/A']})
        res = execute_action("coerce_numeric", df_str, column="Price")
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[0, 'Price'], 1200.50)
        self.assertEqual(res.df.loc[1, 'Price'], 350.0)
        self.assertTrue(np.isnan(res.df.loc[2, 'Price']))

    def test_coerce_boolean(self):
        # HasPass has ['yes', 'no', 'YES', 'NO', nan]
        res = execute_action("coerce_boolean", self.df, column="HasPass")
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[0, 'HasPass'], 1)
        self.assertEqual(res.df.loc[1, 'HasPass'], 0)
        self.assertEqual(res.df.loc[2, 'HasPass'], 1)
        self.assertEqual(res.df.loc[3, 'HasPass'], 0)
        self.assertTrue(np.isnan(res.df.loc[4, 'HasPass']))

    def test_drop_constant_columns(self):
        res = execute_action("drop_constant_columns", self.df)
        self.assertTrue(res.success)
        self.assertNotIn("Constant", res.df.columns)
        self.assertIn("Age", res.df.columns)

    def test_clamp_negative_values(self):
        res = execute_action("clamp_negative_values", self.df, column="Fare")
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[3, 'Fare'], 0.0)

    def test_fill_placeholders(self):
        res = execute_action("fill_placeholders", self.df, column="Age", placeholder=-1)
        self.assertTrue(res.success)
        self.assertEqual(res.df.loc[1, 'Age'], -1)

    def test_replace_invalid_values(self):
        # Replace values in Fare outside bounds [0, 100] with NaN
        res = execute_action("replace_invalid_values", self.df, column="Fare", min_val=0.0, max_val=100.0)
        self.assertTrue(res.success)
        self.assertTrue(np.isnan(res.df.loc[1, 'Fare']))  # 500 is > 100
        self.assertTrue(np.isnan(res.df.loc[3, 'Fare']))  # -5 is < 0
        self.assertEqual(res.df.loc[0, 'Fare'], 10.0)

    def test_get_python_code(self):
        code = get_action_python_code("median_imputation", column="Age")
        self.assertEqual(code, "df['Age'] = df['Age'].fillna(df['Age'].median())")

        code = get_action_python_code("drop_columns", columns=["ColA", "ColB"])
        self.assertEqual(code, "df.drop(columns=['ColA', 'ColB'], inplace=True)")

    def test_unregistered_action(self):
        res = execute_action("hallucinated_action_name", self.df)
        self.assertFalse(res.success)
        self.assertIn("not registered", res.error_message)

    def test_sandboxing_security_injections(self):
        # Ensure that action arguments cannot cause execution of arbitrary malicious code.
        # Arguments are handled inside type-safe code, not passed to exec() or eval().
        malicious_arg = "__import__('os').system('calc')"
        res = execute_action("median_imputation", self.df, column=malicious_arg)
        self.assertFalse(res.success)
        self.assertIn("not found", res.error_message)

if __name__ == '__main__':
    unittest.main()
