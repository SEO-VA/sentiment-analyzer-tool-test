# modules/text_processing.py

import re
from typing import List, Dict, Any

def split_sentences(text: str) -> List[Dict[str, Any]]:
    """
    Split text into sentences with improved handling
    Returns list of {"idx": int, "content": str} dictionaries
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Use simpler approach: split on sentence endings, then filter false positives
    sentences = re.split(r'[.!?]+\s*', text)
    
    # Filter out empty sentences and common abbreviations
    abbreviations = {
        'Mr', 'Ms', 'Mrs', 'Dr', 'Prof', 'Sr', 'Jr', 'vs', 'etc', 'i.e', 'e.g', 
        'U.S.A', 'U.K', 'U.N', 'Inc', 'Ltd', 'Corp', 'Co'
    }
    
    result = []
    idx = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Check if this looks like an abbreviation fragment
            words = sentence.split()
            if len(words) == 1 and words[0] in abbreviations:
                continue
            
            # Skip very short fragments that are likely splitting errors
            if len(sentence) < 3:
                continue
            
            result.append({"idx": idx, "content": sentence})
            idx += 1
    
    return result

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing
    """
    if not text:
        return ""
    
    # Trim whitespace
    text = text.strip()
    
    # Normalize line endings
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # Collapse multiple spaces but preserve single line breaks
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Collapse multiple line breaks to maximum of 2
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation for API planning
    Approximately 4 characters = 1 token
    """
    return max(1, len(text) // 4)