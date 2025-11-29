"""
File Service
Industrial-grade service for file handling operations
Supports Excel and CSV files with validation and error handling
"""

import io
import logging
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import pandas as pd

from config.settings import Settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileValidationResult:
    """Data class for file validation results"""
    is_valid: bool
    message: str
    warnings: List[str]


@dataclass
class FileInfo:
    """Data class for file information"""
    filename: str
    file_type: str
    size_bytes: int
    size_formatted: str
    row_count: int
    column_count: int
    columns: List[str]


class FileService:
    """
    Service class for file operations
    Handles reading, validating, and processing Excel/CSV files
    """
    
    def __init__(self):
        """Initialize File Service"""
        self.settings = Settings()
        self.allowed_extensions = self.settings.file.allowed_extensions
        self.max_file_size_mb = self.settings.file.max_file_size_mb
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    
    def validate_file(self, file, filename: str) -> FileValidationResult:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            filename: Name of the file
            
        Returns:
            FileValidationResult object
        """
        warnings = []
        
        # Check if file exists
        if file is None:
            return FileValidationResult(
                is_valid=False,
                message="No file provided",
                warnings=[]
            )
        
        # Check extension
        if not self.settings.validate_file_extension(filename):
            allowed = ", ".join(self.allowed_extensions)
            return FileValidationResult(
                is_valid=False,
                message=f"Invalid file type. Allowed types: {allowed}",
                warnings=[]
            )
        
        # Check file size
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = self.max_file_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return FileValidationResult(
                    is_valid=False,
                    message=f"File too large. Maximum size: {self.max_file_size_mb} MB",
                    warnings=[]
                )
            
            if file_size > max_size_bytes * 0.8:
                warnings.append(f"Large file detected ({self.format_file_size(file_size)}). Processing may take longer.")
                
        except Exception as e:
            logger.warning(f"Could not determine file size: {e}")
        
        return FileValidationResult(
            is_valid=True,
            message="File validation successful",
            warnings=warnings
        )
    
    def read_file(self, file, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read file into DataFrame
        
        Args:
            file: Uploaded file object
            filename: Name of the file
            
        Returns:
            Tuple of (DataFrame or None, error message or None)
        """
        try:
            # Reset file position
            file.seek(0)
            
            # Read based on file type
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return None, f"Unsupported file format: {filename}"
            
            # Basic validation
            if df.empty:
                return None, "File is empty or contains no data"
            
            if len(df.columns) == 0:
                return None, "File has no columns"
            
            logger.info(f"Successfully read file: {filename} ({len(df)} rows, {len(df.columns)} columns)")
            return df, None
            
        except pd.errors.EmptyDataError:
            return None, "File is empty"
        except pd.errors.ParserError as e:
            return None, f"Error parsing file: {str(e)}"
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None, f"Error reading file: {str(e)}"
    
    def get_file_info(self, file, filename: str, df: pd.DataFrame) -> FileInfo:
        """
        Get file information
        
        Args:
            file: Uploaded file object
            filename: Name of the file
            df: DataFrame read from file
            
        Returns:
            FileInfo object
        """
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
        except:
            file_size = 0
        
        file_type = filename.rsplit('.', 1)[-1].upper() if '.' in filename else "Unknown"
        
        return FileInfo(
            filename=filename,
            file_type=file_type,
            size_bytes=file_size,
            size_formatted=self.format_file_size(file_size),
            row_count=len(df),
            column_count=len(df.columns),
            columns=df.columns.tolist()
        )
    
    def find_transcript_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Attempt to find the transcript column in the DataFrame
        
        Args:
            df: DataFrame to search
            
        Returns:
            Column name if found, None otherwise
        """
        # Common patterns for transcript columns
        patterns = [
            'transcript', 'call', 'conversation', 'text', 'content',
            'dialogue', 'dialog', 'message', 'recording', 'audio_text'
        ]
        
        for col in df.columns:
            col_lower = col.lower()
            for pattern in patterns:
                if pattern in col_lower:
                    return col
        
        return None
    
    def find_id_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Attempt to find the ID column in the DataFrame
        
        Args:
            df: DataFrame to search
            
        Returns:
            Column name if found, None otherwise
        """
        # Common patterns for ID columns
        patterns = [
            'transcript_id', 'call_id', 'id', 'record_id', 'case_id',
            'claim_id', 'reference', 'ref', 'number', 'no'
        ]
        
        for col in df.columns:
            col_lower = col.lower().replace(' ', '_')
            for pattern in patterns:
                if pattern in col_lower:
                    return col
        
        # Check if first column might be an ID
        if len(df.columns) > 0:
            first_col = df.columns[0]
            if df[first_col].dtype in ['int64', 'object'] and df[first_col].nunique() == len(df):
                return first_col
        
        return None
    
    def export_to_excel(self, df: pd.DataFrame, sheet_name: str = "Analysis Results") -> io.BytesIO:
        """
        Export DataFrame to Excel file
        
        Args:
            df: DataFrame to export
            sheet_name: Name of the Excel sheet
            
        Returns:
            BytesIO object containing the Excel file
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            
            # Auto-adjust column widths
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                max_length = min(max_length, 50)  # Cap at 50 characters
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
        
        output.seek(0)
        return output
    
    def export_to_csv(self, df: pd.DataFrame) -> io.BytesIO:
        """
        Export DataFrame to CSV file
        
        Args:
            df: DataFrame to export
            
        Returns:
            BytesIO object containing the CSV file
        """
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output
    
    def prepare_results_dataframe(
        self,
        original_df: pd.DataFrame,
        analysis_results: List[Dict[str, Any]],
        num_rows: int
    ) -> pd.DataFrame:
        """
        Prepare results DataFrame by combining original data with analysis results
        
        Args:
            original_df: Original DataFrame
            analysis_results: List of analysis result dictionaries
            num_rows: Number of rows processed
            
        Returns:
            Combined DataFrame with analysis results
        """
        processed_rows = []
        
        for idx, result in enumerate(analysis_results[:num_rows]):
            if idx < len(original_df):
                row = original_df.iloc[idx].to_dict()
                row['Missing_Elements'] = "; ".join(result.get('missing_elements', []))
                row['Compliance_Severity'] = result.get('severity', 'Unknown')
                row['Analysis_Summary'] = result.get('summary', '')
                processed_rows.append(row)
        
        return pd.DataFrame(processed_rows)
