import re
import hashlib
from typing import List, Dict, Any
from config.settings import NORMALIZATION_SETTINGS, SENTENCE_SPLIT_SETTINGS

class TextProcessor:
    """Handles text normalization, sentence splitting, and hashing"""
    
    def __init__(self):
        self.abbreviations = SENTENCE_SPLIT_SETTINGS['common_abbreviations']
    
    def normalize_text(self, text: str) -> tuple[str, List[str]]:
        """
        Normalize text according to specification
        Returns: (normalized_text, list_of_changes)
        """
        changes = []
        original = text
        
        # Trim whitespace
        text = text.strip()
        if original != text:
            changes.append("Trimmed leading/trailing whitespace")
        
        # Collapse multiple spaces to single
        old_text = text
        text = re.sub(r' +', ' ', text)
        if old_text != text:
            changes.append("Collapsed multiple spaces")
        
        # Normalize newlines to \n
        old_text = text
        text = re.sub(r'\r\n|\r', '\n', text)
        if old_text != text:
            changes.append("Normalized newlines to \\n")
        
        # Keep casing, punctuation, €, %, and diacritics as-is
        # (No changes needed - specification says to preserve these)
        
        return text, changes
    
    def split_sentences(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into sentences with language-agnostic approach
        Returns list of {text: str, hash: str} dictionaries
        """
        sentences = []
        
        # Split on sentence endings followed by whitespace + capital/digit
        # Avoid splitting decimals, abbreviations, percentages
        pattern = r'([.!?]+)(\s+)([A-Z0-9])'
        
        parts = re.split(pattern, text)
        
        if len(parts) == 1:
            # No sentence breaks found, return the whole text as one sentence
            normalized_text, _ = self.normalize_text(text)
            return [{
                'text': text.strip(),
                'hash': self._hash_text(normalized_text)
            }] if text.strip() else []
        
        current_sentence = ""
        i = 0
        
        while i < len(parts):
            if i == 0:
                # First part
                current_sentence = parts[i]
                i += 1
            elif i + 2 < len(parts) and re.match(r'[.!?]+', parts[i]):
                # This is a sentence ending
                ending = parts[i]
                whitespace = parts[i + 1]
                next_char = parts[i + 2]
                
                # Check if this should be split
                should_split = True
                
                # Don't split decimals like "3.14"
                if ending == '.' and current_sentence and current_sentence[-1].isdigit():
                    should_split = False
                
                # Don't split common abbreviations
                words = current_sentence.split()
                if words and any(words[-1].lower().rstrip('.') == abbr for abbr in self.abbreviations):
                    should_split = False
                
                # Don't split percentages like "100 %"
                if ending == '.' and re.search(r'\d\s*%\s*$', current_sentence):
                    should_split = False
                
                if should_split:
                    # Complete current sentence and start new one
                    current_sentence += ending
                    sentence_text = current_sentence.strip()
                    if sentence_text:
                        normalized, _ = self.normalize_text(sentence_text)
                        sentences.append({
                            'text': sentence_text,
                            'hash': self._hash_text(normalized)
                        })
                    current_sentence = next_char
                    i += 3
                else:
                    # Don't split, continue building current sentence
                    current_sentence += ending + whitespace + next_char
                    i += 3
            else:
                # Regular part, add to current sentence
                current_sentence += parts[i]
                i += 1
        
        # Add the last sentence if there's content
        if current_sentence.strip():
            normalized, _ = self.normalize_text(current_sentence.strip())
            sentences.append({
                'text': current_sentence.strip(),
                'hash': self._hash_text(normalized)
            })
        
        return sentences
    
    def _hash_text(self, text: str) -> str:
        """Generate SHA1 hash of normalized text"""
        return hashlib.sha1(text.encode('utf-8')).hexdigest()
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 characters ≈ 1 token)
        Used for batching decisions
        """
        return len(text) // 4
    
    def validate_sentence_bounds(self, sentence: str, spans: List[Dict]) -> bool:
        """
        Validate that spans fully cover the sentence with no overlaps
        Returns True if valid, False otherwise
        """
        if not spans:
            return False
        
        # Sort spans by start position
        sorted_spans = sorted(spans, key=lambda x: x['start'])
        
        # Check bounds and coverage
        sentence_len = len(sentence)
        
        # First span should start at 0
        if sorted_spans[0]['start'] != 0:
            return False
        
        # Last span should end at sentence length
        if sorted_spans[-1]['end'] != sentence_len:
            return False
        
        # Check for gaps or overlaps
        for i in range(len(sorted_spans)):
            span = sorted_spans[i]
            
            # Check individual span bounds
            if span['start'] < 0 or span['end'] > sentence_len or span['start'] >= span['end']:
                return False
            
            # Check for overlap with next span
            if i + 1 < len(sorted_spans):
                next_span = sorted_spans[i + 1]
                if span['end'] > next_span['start']:
                    return False
                # Check for gaps
                if span['end'] < next_span['start']:
                    return False
        
        return True