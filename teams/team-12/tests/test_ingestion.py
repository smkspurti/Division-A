# -*- coding: utf-8 -*-
"""
Ingestion Ingestion and Delimiter/Encoding Parsing Unit Tests.
"""

import os
import unittest
import tempfile
import pandas as pd
import numpy as np
from utils import smart_load_csv, detect_encoding, detect_delimiter, normalize_sentinels

class TestIngestion(unittest.TestCase):
    
    def setUp(self):
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def create_temp_csv(self, content: str, encoding: str = 'utf-8') -> str:
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)
        self.temp_files.append(path)
        return path

    def test_standard_csv_comma(self):
        content = "Name,Age,Class\nAlice,25,A\nBob,30,B\nCharlie,35,C"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        self.assertEqual(meta['delimiter'], ',')
        self.assertEqual(meta['encoding'], 'utf-8')
        self.assertEqual(df.shape, (3, 3))
        self.assertListEqual(list(df.columns), ['Name', 'Age', 'Class'])

    def test_semicolon_delimiter(self):
        content = "Name;Age;Class\nAlice;25;A\nBob;30;B\n"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        self.assertEqual(meta['delimiter'], ';')
        self.assertEqual(df.shape, (2, 3))

    def test_tab_delimiter(self):
        content = "Name\tAge\tClass\nAlice\t25\tA\nBob\t30\tB\n"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        self.assertEqual(meta['delimiter'], '\t')
        self.assertEqual(df.shape, (2, 3))

    def test_pipe_delimiter(self):
        content = "Name|Age|Class\nAlice|25|A\nBob|30|B\n"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        self.assertEqual(meta['delimiter'], '|')
        self.assertEqual(df.shape, (2, 3))

    def test_utf8_bom_encoding(self):
        content = "Name,Age\nAlice,25\n"
        path = self.create_temp_csv(content, encoding='utf-8-sig')
        df, meta = smart_load_csv(path)
        
        self.assertEqual(meta['encoding'], 'utf-8')
        self.assertListEqual(list(df.columns), ['Name', 'Age'])

    def test_iso_8859_encoding(self):
        # Create characters valid in Latin-1 but not ASCII
        content = "Name,City\nRené,Montréal\n"
        path = self.create_temp_csv(content, encoding='iso-8859-1')
        df, meta = smart_load_csv(path)
        
        self.assertIn(meta['encoding'].lower(), ['iso-8859-1', 'windows-1252', 'utf-8'])
        self.assertEqual(df.iloc[0]['Name'], 'René')

    def test_sentinel_null_normalization(self):
        # We test various sentinels like '?', 'N/A', '-', 'None', etc.
        content = "Name,Age,Score,Status\nAlice,?,95.5,Active\nBob,28,N/A,None\nCharlie,32,90.0,-\nDavid,na,85.0,nil"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        # Verify nulls are coerced to NaNs
        self.assertTrue(pd.isna(df.loc[0, 'Age']))
        self.assertTrue(pd.isna(df.loc[1, 'Score']))
        self.assertTrue(pd.isna(df.loc[1, 'Status']))
        self.assertTrue(pd.isna(df.loc[2, 'Status']))
        self.assertTrue(pd.isna(df.loc[3, 'Age']))
        self.assertTrue(pd.isna(df.loc[3, 'Status']))
        
        # Verify that numeric coercion happened on columns that contain numeric values post-null-normalization
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Score']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['Age']))

    def test_leading_trailing_spaces_stripping(self):
        content = "  Name  , Age , Class \n Alice , 25 , A \n"
        path = self.create_temp_csv(content)
        df, meta = smart_load_csv(path)
        
        # Columns and values should be stripped of whitespace
        self.assertListEqual(list(df.columns), ['Name', 'Age', 'Class'])
        self.assertEqual(df.loc[0, 'Name'], 'Alice')
        self.assertEqual(df.loc[0, 'Class'], 'A')

    def test_path_traversal_denied(self):
        # Path outside allowed directory should raise PermissionError
        # System directory like C:/Windows/win.ini on Windows is typical
        bad_path = "C:/Windows/win.ini"
        if os.path.exists(bad_path):
            with self.assertRaises(PermissionError):
                smart_load_csv(bad_path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            smart_load_csv("non_existent_file_path_1234.csv")

if __name__ == '__main__':
    unittest.main()
