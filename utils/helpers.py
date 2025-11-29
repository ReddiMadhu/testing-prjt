"""
Helper Utilities
Common helper functions for the application
"""

import re
import hashlib
from datetime import datetime
from typing import Any, Optional, Dict, List, Union


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s" or "1h 5m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def generate_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Generate timestamp string
    
    Args:
        format_str: strftime format string
        
    Returns:
        Formatted timestamp
    """
    return datetime.now().strftime(format_str)


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid chars with
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "untitled"
    
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")
    
    # Limit length
    max_length = 200
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        name = name[:max_length - len(ext) - 1]
        sanitized = f"{name}.{ext}" if ext else name
    
    return sanitized or "untitled"


def safe_get(
    data: Union[Dict, List, Any],
    key: Union[str, int],
    default: Any = None
) -> Any:
    """
    Safely get value from dict or list
    
    Args:
        data: Dictionary or list to get value from
        key: Key (for dict) or index (for list)
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    try:
        if isinstance(data, dict):
            return data.get(key, default)
        elif isinstance(data, (list, tuple)):
            return data[key] if 0 <= key < len(data) else default
        return default
    except (TypeError, IndexError, KeyError):
        return default


def generate_hash(content: str, length: int = 8) -> str:
    """
    Generate short hash from content
    
    Args:
        content: Content to hash
        length: Length of hash to return
        
    Returns:
        Short hash string
    """
    full_hash = hashlib.md5(content.encode()).hexdigest()
    return full_hash[:length]


def clean_transcript(transcript: str) -> str:
    """
    Clean and normalize transcript text
    
    Args:
        transcript: Raw transcript text
        
    Returns:
        Cleaned transcript
    """
    if not transcript:
        return ""
    
    # Convert to string if not already
    transcript = str(transcript)
    
    # Remove excessive whitespace
    transcript = re.sub(r'\s+', ' ', transcript)
    
    # Remove leading/trailing whitespace
    transcript = transcript.strip()
    
    return transcript


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction (remove common words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can',
        'will', 'just', 'should', 'now', 'i', 'you', 'he', 'she', 'it', 'we',
        'they', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'ought',
        'im', 'youre', 'hes', 'shes', 'its', 'were', 'theyre', 'ive', 'youve',
        'weve', 'theyve', 'id', 'youd', 'hed', 'shed', 'wed', 'theyd', 'ill',
        'youll', 'hell', 'shell', 'well', 'theyll', 'isnt', 'arent', 'wasnt',
        'werent', 'hasnt', 'havent', 'hadnt', 'doesnt', 'dont', 'didnt', 'wont',
        'wouldnt', 'shouldnt', 'couldnt', 'mightnt', 'mustnt', 'okay', 'ok',
        'yeah', 'yes', 'no', 'um', 'uh', 'like', 'know', 'think', 'right'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter and count
    word_counts = {}
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


def format_number(num: Union[int, float], precision: int = 1) -> str:
    """
    Format number with K/M/B suffixes
    
    Args:
        num: Number to format
        precision: Decimal precision
        
    Returns:
        Formatted number string
    """
    if num is None:
        return "0"
    
    abs_num = abs(num)
    sign = "-" if num < 0 else ""
    
    if abs_num >= 1_000_000_000:
        return f"{sign}{abs_num / 1_000_000_000:.{precision}f}B"
    elif abs_num >= 1_000_000:
        return f"{sign}{abs_num / 1_000_000:.{precision}f}M"
    elif abs_num >= 1_000:
        return f"{sign}{abs_num / 1_000:.{precision}f}K"
    else:
        return f"{sign}{abs_num:,.0f}"


def calculate_percentage(part: float, whole: float, decimals: int = 1) -> float:
    """
    Calculate percentage safely
    
    Args:
        part: Part value
        whole: Whole value
        decimals: Number of decimal places
        
    Returns:
        Percentage value
    """
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, decimals)
