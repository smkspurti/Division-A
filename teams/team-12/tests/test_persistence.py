# -*- coding: utf-8 -*-
"""
Persistence Layer and snapshot Restoration Unit Tests.
"""

import os
import shutil
import unittest
import tempfile
import pandas as pd
import numpy as np
from persistence import SessionStore

class TestPersistence(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = SessionStore(db_dir=self.temp_dir)
        self.session_id = "test_session_12345"
        self.df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4.5, np.nan, 6.7],
            'C': ['foo', 'bar', 'baz']
        })

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(self.store.db_path))
        
        # Test direct connections
        with self.store._get_connection() as conn:
            # Verify tables exist
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t['name'] for t in tables]
            self.assertIn('sessions', table_names)
            self.assertIn('action_traces', table_names)
            self.assertIn('profiles', table_names)

    def test_session_creation(self):
        self.store.create_session(self.session_id, "mock_data.csv")
        sessions = self.store.get_all_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['session_id'], self.session_id)
        self.assertEqual(sessions[0]['original_filename'], "mock_data.csv")
        self.assertEqual(sessions[0]['current_step'], 0)

        # Check session snapshot folder was created
        session_folder = os.path.join(self.temp_dir, self.session_id)
        self.assertTrue(os.path.exists(session_folder))

    def test_save_and_retrieve_action_history(self):
        self.store.create_session(self.session_id, "mock_data.csv")
        
        # Save step 1
        self.store.save_action(
            session_id=self.session_id,
            step=1,
            action_name="median_imputation",
            action_args={"column": "B"},
            justification="Imputed missing values in B.",
            code="df['B'] = df['B'].fillna(df['B'].median())"
        )
        
        # Save step 2
        self.store.save_action(
            session_id=self.session_id,
            step=2,
            action_name="drop_columns",
            action_args={"columns": ["C"]},
            justification="Dropped constant column C.",
            code="df.drop(columns=['C'], inplace=True)"
        )
        
        history = self.store.get_session_history(self.session_id)
        self.assertEqual(len(history), 2)
        
        # Verify order and content
        self.assertEqual(history[0]['step'], 1)
        self.assertEqual(history[0]['action_name'], "median_imputation")
        self.assertEqual(history[0]['action_args'], {"column": "B"})
        
        self.assertEqual(history[1]['step'], 2)
        self.assertEqual(history[1]['action_name'], "drop_columns")
        
        # Verify current step updated
        sessions = self.store.get_all_sessions()
        self.assertEqual(sessions[0]['current_step'], 2)

    def test_save_and_retrieve_profile(self):
        self.store.create_session(self.session_id, "mock_data.csv")
        mock_profile = {
            "overall_score": 85.5,
            "columns": {
                "A": {"dtype": "int64", "null_count": 0}
            }
        }
        
        self.store.save_profile(self.session_id, 1, mock_profile)
        retrieved = self.store.get_latest_profile(self.session_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['overall_score'], 85.5)
        self.assertEqual(retrieved['columns']['A']['dtype'], "int64")

    def test_dataframe_snapshot_saving_and_loading(self):
        self.store.create_session(self.session_id, "mock_data.csv")
        
        # Save snapshot
        file_path = self.store.save_dataframe_snapshot(self.session_id, 1, self.df)
        self.assertTrue(os.path.exists(file_path))
        self.assertIn("step_1.parquet", file_path)
        
        # Load snapshot
        loaded_df = self.store.load_dataframe_snapshot(self.session_id, 1)
        self.assertEqual(loaded_df.shape, self.df.shape)
        self.assertListEqual(list(loaded_df.columns), list(self.df.columns))
        self.assertEqual(loaded_df.loc[0, 'A'], 1)
        self.assertTrue(np.isnan(loaded_df.loc[1, 'B']))
        self.assertEqual(loaded_df.loc[2, 'C'], 'baz')

    def test_delete_session(self):
        self.store.create_session(self.session_id, "mock_data.csv")
        self.store.save_dataframe_snapshot(self.session_id, 1, self.df)
        
        # Delete it
        self.store.delete_session(self.session_id)
        
        # Check database records are gone
        sessions = self.store.get_all_sessions()
        self.assertEqual(len(sessions), 0)
        
        # Check files are cleaned up from disk
        session_folder = os.path.join(self.temp_dir, self.session_id)
        self.assertFalse(os.path.exists(session_folder))

if __name__ == '__main__':
    unittest.main()
