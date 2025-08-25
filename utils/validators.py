import json
from typing import List, Dict, Any, Optional

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class ResponseValidator:
    """Validates LLM responses against expected schemas"""
    
    @staticmethod
    def validate_stage1_response(response_data: List[Dict], input_length: int) -> List[str]:
        """
        Validate Stage 1 LLM response
        Returns list of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Check if it's a list
            if not isinstance(response_data, list):
                errors.append("Response must be a list")
                return errors
            
            # Check length matches input
            if len(response_data) != input_length:
                errors.append(f"Response length ({len(response_data)}) doesn't match input length ({input_length})")
            
            # Validate each item
            for i, item in enumerate(response_data):
                if not isinstance(item, dict):
                    errors.append(f"Item {i} must be a dictionary")
                    continue
                
                # Check required fields
                required_fields = ['hash', 'label']
                for field in required_fields:
                    if field not in item:
                        errors.append(f"Item {i} missing required field: {field}")
                
                # Validate label
                if 'label' in item and item['label'] not in ['info', 'promo', 'risk']:
                    errors.append(f"Item {i} has invalid label: {item['label']}")
                
                # Validate needs_phrase_level if present
                if 'needs_phrase_level' in item and not isinstance(item['needs_phrase_level'], bool):
                    errors.append(f"Item {i} needs_phrase_level must be boolean")
        
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_stage2_response(response_data: List[Dict], sentences: List[Dict]) -> List[str]:
        """
        Validate Stage 2 LLM response
        Returns list of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Check if it's a list
            if not isinstance(response_data, list):
                errors.append("Response must be a list")
                return errors
            
            # Check length matches input
            if len(response_data) != len(sentences):
                errors.append(f"Response length ({len(response_data)}) doesn't match input length ({len(sentences)})")
            
            # Validate each result
            for i, result in enumerate(response_data):
                if not isinstance(result, dict):
                    errors.append(f"Result {i} must be a dictionary")
                    continue
                
                # Check required fields
                required_fields = ['hash', 'spans']
                for field in required_fields:
                    if field not in result:
                        errors.append(f"Result {i} missing required field: {field}")
                        continue
                
                # Validate spans
                if 'spans' in result:
                    span_errors = ResponseValidator._validate_spans(result['spans'], sentences[i]['text'], i)
                    errors.extend(span_errors)
        
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def _validate_spans(spans: List[Dict], sentence_text: str, result_index: int) -> List[str]:
        """Validate spans for a single sentence"""
        errors = []
        sentence_len = len(sentence_text)
        
        if not isinstance(spans, list):
            errors.append(f"Result {result_index} spans must be a list")
            return errors
        
        if not spans:
            errors.append(f"Result {result_index} spans cannot be empty")
            return errors
        
        # Sort spans for validation
        try:
            sorted_spans = sorted(spans, key=lambda x: x['start'])
        except (KeyError, TypeError):
            errors.append(f"Result {result_index} spans have invalid structure")
            return errors
        
        # Validate each span
        for j, span in enumerate(sorted_spans):
            if not isinstance(span, dict):
                errors.append(f"Result {result_index} span {j} must be a dictionary")
                continue
            
            # Check required fields
            span_fields = ['start', 'end', 'label']
            for field in span_fields:
                if field not in span:
                    errors.append(f"Result {result_index} span {j} missing field: {field}")
            
            # Validate bounds
            if 'start' in span and 'end' in span:
                start, end = span['start'], span['end']
                
                if not isinstance(start, int) or not isinstance(end, int):
                    errors.append(f"Result {result_index} span {j} start/end must be integers")
                    continue
                
                if start < 0 or end > sentence_len or start >= end:
                    errors.append(f"Result {result_index} span {j} invalid bounds: {start}-{end} for sentence length {sentence_len}")
            
            # Validate label
            if 'label' in span and span['label'] not in ['info', 'promo', 'risk']:
                errors.append(f"Result {result_index} span {j} invalid label: {span['label']}")
        
        # Validate coverage and no overlaps
        coverage_errors = ResponseValidator._validate_span_coverage(sorted_spans, sentence_len, result_index)
        errors.extend(coverage_errors)
        
        return errors
    
    @staticmethod
    def _validate_span_coverage(spans: List[Dict], sentence_len: int, result_index: int) -> List[str]:
        """Validate that spans provide full coverage with no overlaps or gaps"""
        errors = []
        
        if not spans:
            return [f"Result {result_index} has no spans"]
        
        try:
            # Check first span starts at 0
            if spans[0]['start'] != 0:
                errors.append(f"Result {result_index} first span must start at 0, got {spans[0]['start']}")
            
            # Check last span ends at sentence length
            if spans[-1]['end'] != sentence_len:
                errors.append(f"Result {result_index} last span must end at {sentence_len}, got {spans[-1]['end']}")
            
            # Check for gaps or overlaps
            for i in range(len(spans) - 1):
                current_end = spans[i]['end']
                next_start = spans[i + 1]['start']
                
                if current_end > next_start:
                    errors.append(f"Result {result_index} spans {i} and {i+1} overlap")
                elif current_end < next_start:
                    errors.append(f"Result {result_index} gap between spans {i} and {i+1}")
        
        except (KeyError, IndexError) as e:
            errors.append(f"Result {result_index} span structure error: {str(e)}")
        
        return errors

class JSONValidator:
    """Validates JSON responses from LLM"""
    
    @staticmethod
    def parse_and_validate_json(response_text: str) -> tuple[Any, Optional[str]]:
        """
        Parse JSON response and return (data, error_message)
        Returns (None, error_message) if parsing fails
        """
        try:
            data = json.loads(response_text)
            return data, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return None, f"JSON parsing error: {str(e)}"
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> tuple[Any, Optional[str]]:
        """
        Try to extract JSON from response that might have extra text
        Sometimes LLMs add explanations around the JSON
        """
        # First try direct parsing
        data, error = JSONValidator.parse_and_validate_json(response_text)
        if data is not None:
            return data, None
        
        # Try to find JSON within the response
        import re
        
        # Look for JSON array patterns
        array_matches = re.findall(r'\[.*\]', response_text, re.DOTALL)
        for match in array_matches:
            data, _ = JSONValidator.parse_and_validate_json(match)
            if data is not None:
                return data, None
        
        # Look for JSON object patterns
        object_matches = re.findall(r'\{.*\}', response_text, re.DOTALL)
        for match in object_matches:
            data, _ = JSONValidator.parse_and_validate_json(match)
            if data is not None:
                return data, None
        
        return None, f"No valid JSON found in response: {response_text[:200]}..."