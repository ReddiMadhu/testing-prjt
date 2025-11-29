"""
Validators Module
Input validation utilities for the application
"""

import re
from typing import List, Tuple, Optional
import pandas as pd


class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool, message: str = "", warnings: List[str] = None):
        self.is_valid = is_valid
        self.message = message
        self.warnings = warnings or []
    
    def __bool__(self):
        return self.is_valid


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """
    Validate DataFrame structure and content
    
    Args:
        df: DataFrame to validate
        
    Returns:
        ValidationResult object
    """
    warnings = []
    
    # Check if DataFrame is None or empty
    if df is None:
        return ValidationResult(False, "DataFrame is None")
    
    if df.empty:
        return ValidationResult(False, "DataFrame is empty")
    
    if len(df.columns) == 0:
        return ValidationResult(False, "DataFrame has no columns")
    
    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        warnings.append("DataFrame contains duplicate column names")
    
    # Check for excessive null values
    null_percentages = (df.isnull().sum() / len(df)) * 100
    high_null_cols = null_percentages[null_percentages > 50].index.tolist()
    if high_null_cols:
        warnings.append(f"High null percentage in columns: {', '.join(high_null_cols)}")
    
    # Check for very large DataFrames
    if len(df) > 10000:
        warnings.append(f"Large dataset ({len(df):,} rows) - processing may take longer")
    
    return ValidationResult(True, "DataFrame validation passed", warnings)


def validate_transcript_content(transcript: str) -> ValidationResult:
    """
    Validate transcript content
    
    Args:
        transcript: Transcript text to validate
        
    Returns:
        ValidationResult object
    """
    warnings = []
    
    # Check if transcript is empty or None
    if not transcript:
        return ValidationResult(False, "Transcript is empty")
    
    # Convert to string if needed
    transcript = str(transcript).strip()
    
    if not transcript:
        return ValidationResult(False, "Transcript is empty after stripping whitespace")
    
    # Check minimum length
    if len(transcript) < 50:
        warnings.append("Transcript seems very short - may not contain enough information")
    
    # Check for placeholder text
    placeholder_patterns = [
        r'^(test|sample|placeholder|lorem ipsum)',
        r'^(n/a|na|null|none|empty)$',
        r'^[\s\-\._]+$'
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, transcript.lower()):
            return ValidationResult(False, "Transcript appears to be placeholder text")
    
    # Check for excessive special characters
    special_char_ratio = len(re.findall(r'[^\w\s]', transcript)) / len(transcript)
    if special_char_ratio > 0.3:
        warnings.append("Transcript contains high proportion of special characters")
    
    # Check for likely encoded or corrupted text
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', transcript):
        warnings.append("Transcript may contain corrupted or binary data")
    
    return ValidationResult(True, "Transcript validation passed", warnings)


def validate_column_selection(
    df: pd.DataFrame,
    column_name: str,
    expected_type: str = "text"
) -> ValidationResult:
    """
    Validate selected column for analysis
    
    Args:
        df: DataFrame containing the column
        column_name: Name of column to validate
        expected_type: Expected data type ("text", "numeric", "id")
        
    Returns:
        ValidationResult object
    """
    warnings = []
    
    # Check if column exists
    if column_name not in df.columns:
        return ValidationResult(False, f"Column '{column_name}' not found in DataFrame")
    
    column = df[column_name]
    
    # Check for all null values
    if column.isnull().all():
        return ValidationResult(False, f"Column '{column_name}' contains only null values")
    
    # Check null percentage
    null_pct = column.isnull().sum() / len(column) * 100
    if null_pct > 20:
        warnings.append(f"Column has {null_pct:.1f}% null values")
    
    if expected_type == "text":
        # Validate text column
        non_null = column.dropna()
        
        # Check if values are strings
        non_string_count = sum(not isinstance(x, str) for x in non_null)
        if non_string_count > 0:
            warnings.append(f"{non_string_count} values are not strings")
        
        # Check average length
        avg_length = non_null.astype(str).str.len().mean()
        if avg_length < 20:
            warnings.append(f"Average text length is very short ({avg_length:.0f} characters)")
        
    elif expected_type == "numeric":
        # Validate numeric column
        if not pd.api.types.is_numeric_dtype(column):
            # Try to convert
            try:
                pd.to_numeric(column.dropna(), errors='raise')
                warnings.append("Column will be converted to numeric")
            except (ValueError, TypeError):
                return ValidationResult(False, f"Column '{column_name}' cannot be converted to numeric")
    
    elif expected_type == "id":
        # Validate ID column
        unique_count = column.nunique()
        if unique_count != len(column.dropna()):
            warnings.append(f"Column has duplicate values ({unique_count} unique out of {len(column.dropna())} total)")
    
    return ValidationResult(True, "Column validation passed", warnings)


def validate_api_key(api_key: str) -> ValidationResult:
    """
    Validate API key format
    
    Args:
        api_key: API key to validate
        
    Returns:
        ValidationResult object
    """
    if not api_key:
        return ValidationResult(False, "API key is not set")
    
    # Check basic format (Anthropic keys typically start with 'sk-')
    if not api_key.startswith('sk-'):
        return ValidationResult(False, "API key format appears invalid (should start with 'sk-')")
    
    # Check minimum length
    if len(api_key) < 40:
        return ValidationResult(False, "API key appears too short")
    
    return ValidationResult(True, "API key format is valid")


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> ValidationResult:
    """
    Validate file extension
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (without dots)
        
    Returns:
        ValidationResult object
    """
    if not filename:
        return ValidationResult(False, "Filename is empty")
    
    # Extract extension
    if '.' not in filename:
        return ValidationResult(False, "File has no extension")
    
    extension = filename.rsplit('.', 1)[-1].lower()
    
    if extension not in [ext.lower() for ext in allowed_extensions]:
        allowed = ", ".join(f".{ext}" for ext in allowed_extensions)
        return ValidationResult(False, f"File type '.{extension}' not allowed. Allowed types: {allowed}")
    
    return ValidationResult(True, "File extension is valid")


def validate_processing_params(
    num_rows: int,
    max_rows: int,
    total_rows: int
) -> ValidationResult:
    """
    Validate processing parameters
    
    Args:
        num_rows: Number of rows to process
        max_rows: Maximum allowed rows
        total_rows: Total rows in dataset
        
    Returns:
        ValidationResult object
    """
    warnings = []
    
    if num_rows <= 0:
        return ValidationResult(False, "Number of rows must be greater than 0")
    
    if num_rows > max_rows:
        return ValidationResult(False, f"Cannot process more than {max_rows} rows at once")
    
    if num_rows > total_rows:
        warnings.append(f"Requested {num_rows} rows but only {total_rows} available - will process all")
    
    if num_rows > 50:
        warnings.append(f"Processing {num_rows} rows may take several minutes")
    
    return ValidationResult(True, "Processing parameters are valid", warnings)
