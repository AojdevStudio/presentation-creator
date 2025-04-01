"""
Data cleaning and transformation utilities for presentation data.
"""
import re
from typing import Any, Dict, List, Union
import pandas as pd
import numpy as np
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and special characters.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove parentheses and their contents
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s!?.,—]', '', text)
    
    # Normalize quotes and apostrophes
    text = text.replace('"', '').replace('"', '').replace(''', "'").replace(''', "'")
    
    # Normalize dashes
    text = text.replace('--', '—')
    
    return text.strip()

def clean_list(items: List[str]) -> List[str]:
    """
    Clean a list of text items.
    
    Args:
        items (List[str]): List of text items to clean
        
    Returns:
        List[str]: List of cleaned text items with empty items removed
    """
    cleaned = [clean_text(item) for item in items]
    return [item for item in cleaned if item]

def format_bullet_points(points: List[str], max_length: int = 60) -> List[str]:
    """
    Format text as bullet points, splitting long points into multiple lines.
    
    Args:
        points (List[str]): List of text points to format
        max_length (int): Maximum length for each line
        
    Returns:
        List[str]: Formatted bullet points
    """
    formatted_points = []
    
    for point in points:
        point = clean_text(point)
        
        if len(point) <= max_length:
            formatted_points.append(point)
        else:
            # Split long points into multiple lines
            words = point.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_length:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    formatted_points.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                formatted_points.append(' '.join(current_line))
    
    return formatted_points

def clean_numerical_data(data: Union[pd.DataFrame, Dict[str, List[float]]]) -> Dict[str, Any]:
    """
    Clean and format numerical data for presentation.
    
    Args:
        data: Either a pandas DataFrame or dictionary of numerical lists
        
    Returns:
        Dict containing cleaned data and metadata
    """
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data.copy()
    
    # Remove rows where all values are NaN
    df = df.dropna(how='all')
    
    # Fill remaining NaN values with column means
    df = df.fillna(df.mean())
    
    # Round numbers for presentation
    df = df.round(2)
    
    metadata = {
        'row_count': len(df),
        'column_count': len(df.columns),
        'summary_stats': {
            'mean': df.mean().to_dict(),
            'std': df.std().to_dict(),
            'min': df.min().to_dict(),
            'max': df.max().to_dict()
        }
    }
    
    return {
        'data': df.to_dict('list'),
        'metadata': metadata
    }

def extract_key_points(text: str, max_points: int = 5) -> List[str]:
    """
    Extract key points from a text block.
    
    Args:
        text (str): Input text block
        max_points (int): Maximum number of key points to extract
        
    Returns:
        List[str]: Extracted key points
    """
    # Split text into sentences
    sentences = sent_tokenize(text)
    
    # Score sentences based on importance indicators
    stop_words = set(stopwords.words('english'))
    scores = []
    
    for sentence in sentences:
        score = 0
        words = sentence.lower().split()
        
        # Score based on presence of important words/phrases
        importance_indicators = ['key', 'main', 'important', 'significant', 'crucial', 'essential']
        score += sum(2 for word in words if word in importance_indicators)
        
        # Score based on sentence length (prefer medium-length sentences)
        word_count = len([w for w in words if w not in stop_words])
        if 5 <= word_count <= 20:
            score += 1
        
        scores.append((score, sentence))
    
    # Sort by score and take top N points
    scores.sort(reverse=True)
    key_points = [clean_text(sentence) for _, sentence in scores[:max_points]]
    
    return key_points

def format_section_title(title: str) -> str:
    """
    Format a section title with proper capitalization and spacing.
    
    Args:
        title (str): Input title to format
        
    Returns:
        str: Formatted title
    """
    # Clean the title first
    title = clean_text(title.lower())
    
    # List of words to keep lowercase
    lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
                      'on', 'at', 'to', 'from', 'by', 'with', 'in', 'of'}
    
    # Split into words
    words = title.split()
    
    # Capitalize first and last words always, and other words unless they're in lowercase_words
    formatted_words = []
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word not in lowercase_words:
            formatted_words.append(word.capitalize())
        else:
            formatted_words.append(word)
    
    return ' '.join(formatted_words) 