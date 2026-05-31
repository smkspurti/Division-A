import os
import csv
import chardet
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def detect_encoding(file_path: str) -> str:
    """Detects the file encoding of a CSV file using chardet."""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(50000)  # Read first 50KB
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        if encoding is None:
            return 'utf-8'
        # Adjust common mismatches
        if encoding.lower() in ['ascii', 'utf-8-sig']:
            return 'utf-8'
        return encoding
    except Exception:
        return 'utf-8'

def detect_delimiter(file_path: str, encoding: str = 'utf-8') -> str:
    """Detects the column delimiter of a CSV file using csv.Sniffer or falls back to heuristics."""
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            sample = f.read(8192)
        
        # Strip lines to avoid empty lines skewing sniffer
        sample_lines = [line.strip() for line in sample.splitlines() if line.strip()]
        sample_cleaned = '\n'.join(sample_lines[:10])  # Use top 10 lines
        
        dialect = csv.Sniffer().sniff(sample_cleaned)
        return dialect.delimiter
    except Exception:
        # Heuristic search for common separators
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                first_line = f.readline()
            
            delimiters = [',', ';', '\t', '|']
            counts = {d: first_line.count(d) for d in delimiters}
            max_delim = max(counts, key=counts.get)
            if counts[max_delim] > 0:
                return max_delim
        except Exception:
            pass
        return ','

def smart_load_csv(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ingests a raw CSV file by detecting its encoding and delimiter,
    normalizing sentinel nulls, and stripping whitespace from column names.
    Returns the loaded DataFrame and a dictionary of loading metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at {file_path}")
        
    # Security check: Restrict traversal and verify directories
    import tempfile
    abs_path = os.path.normcase(os.path.abspath(file_path))
    allowed_dirs = [
        os.path.normcase(os.path.abspath('.')),
        os.path.normcase(os.path.abspath(tempfile.gettempdir()))
    ]
    if os.environ.get('TEMP'):
        allowed_dirs.append(os.path.normcase(os.path.abspath(os.environ['TEMP'])))
    if os.environ.get('TMP'):
        allowed_dirs.append(os.path.normcase(os.path.abspath(os.environ['TMP'])))
        
    is_allowed = any(abs_path.startswith(d) for d in allowed_dirs if d)
    if not is_allowed:
        raise PermissionError(f"Access denied: file path '{file_path}' is outside the allowed directories.")
        
    # File size validation: 100MB limit to prevent memory overflow
    MAX_CSV_SIZE = 100 * 1024 * 1024
    if os.path.getsize(file_path) > MAX_CSV_SIZE:
        raise ValueError(f"File size exceeds the maximum limit of {MAX_CSV_SIZE / (1024*1024):.1f} MB.")
        
    encoding = detect_encoding(file_path)
    delimiter = detect_delimiter(file_path, encoding)
    
    # Read CSV
    df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, skipinitialspace=True)
    
    # Clean column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]
    
    # Record metadata before modifications
    original_shape = df.shape
    
    # Normalize sentinel nulls
    df = normalize_sentinels(df)
    
    metadata = {
        "encoding": encoding,
        "delimiter": delimiter,
        "original_shape": original_shape,
        "inferred_shape": df.shape,
    }
    
    return df, metadata

def normalize_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies common sentinel null values (e.g., '?', 'N/A', '-') and
    normalizes them to true NaN/None values, while cleaning string columns.
    """
    df = df.copy()
    
    # Common text-based sentinel null values
    sentinel_patterns = {
        '?', 'n/a', 'n.a.', 'na', 'null', 'nil', '-', '--', 'none', '', 'nan', 'missing'
    }
    
    for col in df.columns:
        # Check if the column is categorical/string
        if df[col].dtype == object or isinstance(df[col].dtype, pd.CategoricalDtype):
            # Convert to string, strip whitespace, handle case-insensitiveness
            col_str = df[col].astype(str).str.strip()
            
            # Create a mask for values matching sentinel patterns
            mask = col_str.str.lower().isin(sentinel_patterns) | col_str.isna() | (col_str == 'nan')
            
            # Replace matching values with np.nan
            df.loc[mask, col] = np.nan
            
            # Clean non-null values by stripping whitespaces
            df.loc[~mask, col] = df.loc[~mask, col].astype(str).str.strip()
            
            # Try to convert column back to numeric/float if it is numeric now
            try:
                converted = pd.to_numeric(df[col], errors='raise')
                df[col] = converted
            except (ValueError, TypeError):
                # If raise failed, keep as object/string
                pass
                
    return df
