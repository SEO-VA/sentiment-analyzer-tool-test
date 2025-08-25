import re
from typing import List
from config.settings import HEURISTICS_PATTERNS

class HeuristicsEngine:
    """Determines which sentences need phrase-level analysis using pattern matching"""
    
    def __init__(self):
        self.patterns = HEURISTICS_PATTERNS
        self.last_selection_criteria = []
    
    def should_use_phrase_level(self, text: str) -> bool:
        """
        Determine if a sentence should be analyzed at phrase level
        Returns True if sentence likely contains mixed content types
        """
        criteria_met = []
        
        # Pattern 1: Contains numbers/percentages + action words
        if self._has_numbers_and_actions(text):
            criteria_met.append("numbers_with_actions")
        
        # Pattern 2: Has parenthetical or bracketed text (potential disclaimers)
        if self._has_parenthetical_disclaimers(text):
            criteria_met.append("parenthetical_disclaimers")
        
        # Pattern 3: Mixed descriptive + promotional language
        if self._has_mixed_content_indicators(text):
            criteria_met.append("mixed_content_indicators")
        
        # Pattern 4: Contains risk warnings embedded in promotional text
        if self._has_embedded_risk_warnings(text):
            criteria_met.append("embedded_risk_warnings")
        
        # Pattern 5: Complex sentence structure suggesting multiple content types
        if self._has_complex_mixed_structure(text):
            criteria_met.append("complex_mixed_structure")
        
        self.last_selection_criteria = criteria_met
        return len(criteria_met) > 0
    
    def get_last_selection_criteria(self) -> List[str]:
        """Get the criteria that triggered the last selection"""
        return self.last_selection_criteria
    
    def _has_numbers_and_actions(self, text: str) -> bool:
        """Check for numbers/percentages combined with action words"""
        # Look for percentages, currencies, or numbers
        has_numbers = bool(re.search(r'[\d,]+%|[\d,]+\s*€|\$[\d,]+|[\d,]+\s*(times|x|multiplier)', text, re.IGNORECASE))
        
        # Look for action words
        action_words = self.patterns['action_words']
        has_actions = any(word.lower() in text.lower() for word in action_words)
        
        return has_numbers and has_actions
    
    def _has_parenthetical_disclaimers(self, text: str) -> bool:
        """Check for parenthetical or bracketed text that might be disclaimers"""
        # Look for content in parentheses or brackets
        parenthetical = re.findall(r'\([^)]+\)|\[[^\]]+\]', text)
        
        if not parenthetical:
            return False
        
        # Check if parenthetical content contains disclaimer-like language
        disclaimer_indicators = self.patterns['disclaimer_indicators']
        
        for content in parenthetical:
            content_lower = content.lower()
            if any(indicator in content_lower for indicator in disclaimer_indicators):
                return True
        
        return False
    
    def _has_mixed_content_indicators(self, text: str) -> bool:
        """Check for mixed descriptive and promotional language"""
        # Look for descriptive/informational terms
        info_indicators = self.patterns['info_indicators']
        has_info = any(indicator.lower() in text.lower() for indicator in info_indicators)
        
        # Look for promotional terms
        promo_indicators = self.patterns['promo_indicators']
        has_promo = any(indicator.lower() in text.lower() for indicator in promo_indicators)
        
        return has_info and has_promo
    
    def _has_embedded_risk_warnings(self, text: str) -> bool:
        """Check for risk warnings embedded within promotional content"""
        # Look for risk warning terms
        risk_indicators = self.patterns['risk_indicators']
        has_risk = any(indicator.lower() in text.lower() for indicator in risk_indicators)
        
        # Look for promotional terms in same sentence
        promo_indicators = self.patterns['promo_indicators']
        has_promo = any(indicator.lower() in text.lower() for indicator in promo_indicators)
        
        return has_risk and has_promo
    
    def _has_complex_mixed_structure(self, text: str) -> bool:
        """Check for complex sentence structures suggesting multiple content types"""
        # Look for conjunctions that might separate different content types
        conjunctions = ['but', 'however', 'although', 'while', 'whereas', 'nevertheless', 'nonetheless']
        has_contrasting_conjunction = any(f' {conj} ' in text.lower() for conj in conjunctions)
        
        # Look for dash-separated clauses (common in mixed content)
        has_dash_separation = ' - ' in text or ' – ' in text or ' — ' in text
        
        # Look for semicolon-separated clauses
        has_semicolon_separation = ';' in text
        
        # Check sentence length (very long sentences more likely to be mixed)
        is_long_sentence = len(text.split()) > 25
        
        # Must have structural complexity AND some content variety indicators
        structural_complexity = has_contrasting_conjunction or has_dash_separation or has_semicolon_separation
        
        if not structural_complexity:
            return False
        
        # Check for content variety indicators
        all_indicators = (
            self.patterns['info_indicators'] + 
            self.patterns['promo_indicators'] + 
            self.patterns['risk_indicators']
        )
        
        indicator_count = sum(1 for indicator in all_indicators if indicator.lower() in text.lower())
        
        # Complex structure + multiple different content indicators suggests mixed content
        return structural_complexity and (indicator_count >= 2 or is_long_sentence)