import json
import time
import logging
from typing import List, Dict, Any, Optional
import streamlit as st
from openai import OpenAI
from config.settings import LLM_SETTINGS

logger = logging.getLogger(__name__)

class LLMClient:
    """OpenAI Assistant client for content classification"""
    
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["openai_api_key"])
        self.stage1_assistant_id = st.secrets["assistant_id"]
        self.max_retries = LLM_SETTINGS['max_retries']
    
    def classify_sentences_stage1(self, sentences: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Stage 1: Classify sentences and flag those needing phrase-level analysis
        Input: [{"hash": str, "text": str}, ...]
        Output: [{"hash": str, "label": str, "needs_phrase_level": bool}, ...]
        """
        # Prepare input for assistant
        input_data = {"items": sentences}
        input_json = json.dumps(input_data, ensure_ascii=False)
        
        logger.info(f"Sending to assistant: {len(sentences)} sentences")
        logger.info(f"Input JSON: {input_json}")
        
        # Call assistant with retries
        response = self._call_assistant_with_retry(
            self.stage1_assistant_id,
            input_json
        )
        
        # Parse and validate response
        try:
            logger.info("Parsing Stage 1 JSON response...")
            
            # Try to extract JSON from response (assistant might add explanations)
            json_part = self._extract_json_array(response)
            results = json.loads(json_part)
            
            # Validate response structure
            if not isinstance(results, list):
                logger.error(f"Stage 1 response is not a list: {type(results)}")
                raise ValueError("Stage 1 response must be a list")
            
            if len(results) != len(sentences):
                logger.error(f"Stage 1 length mismatch: got {len(results)}, expected {len(sentences)}")
                raise ValueError(f"Stage 1 response length ({len(results)}) doesn't match input length ({len(sentences)})")
            
            # Validate each result
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    raise ValueError(f"Stage 1 result {i} must be a dict")
                
                required_fields = ['hash', 'label']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Stage 1 result {i} missing required field: {field}")
                
                # Validate label
                if result['label'] not in ['info', 'promo', 'risk']:
                    raise ValueError(f"Stage 1 result {i} has invalid label: {result['label']}")
                
                # Ensure hash matches input order
                if result['hash'] != sentences[i]['hash']:
                    raise ValueError(f"Stage 1 result {i} hash mismatch")
                
                # Set default for needs_phrase_level if not present
                if 'needs_phrase_level' not in result:
                    result['needs_phrase_level'] = False
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Stage 1 JSON parsing failed: {e}")
            logger.error(f"Response text: {response[:500]}...")
            raise ValueError(f"Stage 1 response is not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Stage 1 validation error: {e}")
            raise ValueError(f"Stage 1 validation failed: {e}")
    
    def classify_phrases_stage2(self, sentences: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Stage 2: Generate character spans for mixed-content sentences
        Input: [{"hash": str, "text": str}, ...]
        Output: [{"hash": str, "spans": [{"start": int, "end": int, "label": str}]}, ...]
        """
        if not sentences:
            return []
        
        # Prepare input for assistant
        input_data = {"sentences": sentences}
        
        # Call assistant with retries
        response = self._call_assistant_with_retry(
            self.stage2_assistant_id,
            json.dumps(input_data, ensure_ascii=False)
        )
        
        # Parse and validate response
        try:
            logger.info("Parsing Stage 2 JSON response...")
            
            # Try to extract JSON from response (assistant might add explanations)
            json_part = self._extract_json_array(response)
            results = json.loads(json_part)
            
            # Validate response structure
            if not isinstance(results, list):
                raise ValueError("Stage 2 response must be a list")
            
            if len(results) != len(sentences):
                raise ValueError(f"Stage 2 response length ({len(results)}) doesn't match input length ({len(sentences)})")
            
            # Validate each result
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    raise ValueError(f"Stage 2 result {i} must be a dict")
                
                required_fields = ['hash', 'spans']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Stage 2 result {i} missing required field: {field}")
                
                # Ensure hash matches input order
                if result['hash'] != sentences[i]['hash']:
                    raise ValueError(f"Stage 2 result {i} hash mismatch")
                
                # Validate spans
                spans = result['spans']
                if not isinstance(spans, list):
                    raise ValueError(f"Stage 2 result {i} spans must be a list")
                
                sentence_text = sentences[i]['text']
                sentence_len = len(sentence_text)
                
                for j, span in enumerate(spans):
                    if not isinstance(span, dict):
                        raise ValueError(f"Stage 2 result {i} span {j} must be a dict")
                    
                    # Check required fields
                    span_fields = ['start', 'end', 'label']
                    for field in span_fields:
                        if field not in span:
                            raise ValueError(f"Stage 2 result {i} span {j} missing field: {field}")
                    
                    # Validate bounds
                    start, end = span['start'], span['end']
                    
                    if not isinstance(start, int) or not isinstance(end, int):
                        raise ValueError(f"Stage 2 result {i} span {j} start/end must be integers")
                    
                    if start < 0 or end > sentence_len or start >= end:
                        raise ValueError(f"Stage 2 result {i} span {j} invalid bounds: {start}-{end} for length {sentence_len}")
                    
                    # Validate label
                    if span['label'] not in ['info', 'promo', 'risk']:
                        raise ValueError(f"Stage 2 result {i} span {j} invalid label: {span['label']}")
                
                # Validate span coverage and ordering
                from core.text_processor import TextProcessor
                processor = TextProcessor()
                if not processor.validate_sentence_bounds(sentence_text, spans):
                    raise ValueError(f"Stage 2 result {i} spans don't provide full coverage or have overlaps")
            
            return results
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Stage 2 response is not valid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Stage 2 validation failed: {e}")
    
    def _call_assistant_with_retry(self, assistant_id: str, message: str) -> str:
        """
        Call OpenAI assistant with retry logic
        Returns the assistant's response text
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Create a thread
                thread = self.client.beta.threads.create()
                
                # Add message to thread
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Run the assistant
                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant_id
                )
                
                # Wait for completion
                while run.status in ['queued', 'in_progress']:
                    time.sleep(1)
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                if run.status == 'completed':
                    # Get the assistant's response
                    messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                    assistant_message = messages.data[0]  # Latest message
                    
                    if assistant_message.role == 'assistant':
                        response_text = assistant_message.content[0].text.value
                        logger.info(f"LLM response received: {len(response_text)} chars")
                        logger.info(f"Response preview: {response_text[:200]}...")
                        return response_text
                    else:
                        raise Exception("Expected assistant response but got user message")
                
                elif run.status == 'failed':
                    raise Exception(f"Assistant run failed: {run.last_error}")
                else:
                    raise Exception(f"Assistant run ended with status: {run.status}")
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) + 1
                    time.sleep(wait_time)
                    continue
                else:
                    break
        
        # All retries failed
        logger.error(f"LLM call failed after {self.max_retries} attempts: {last_error}")
        raise Exception(f"Failed to get response from assistant after {self.max_retries} attempts. Last error: {last_error}")
    
    def estimate_batch_size(self, sentences: List[Dict[str, str]]) -> int:
        """
        Estimate appropriate batch size based on total token count
        Returns suggested batch size
        """
        from core.text_processor import TextProcessor
        processor = TextProcessor()
        
        total_tokens = sum(processor.estimate_tokens(s['text']) for s in sentences)
        
        # Target ~4000 tokens per batch
        target_tokens_per_batch = LLM_SETTINGS['target_tokens_per_batch']
        
        if total_tokens <= target_tokens_per_batch:
            return len(sentences)  # Process all in one batch
        
        # Calculate sentences per batch based on average tokens per sentence
        avg_tokens_per_sentence = total_tokens / len(sentences)
        sentences_per_batch = max(1, int(target_tokens_per_batch / avg_tokens_per_sentence))
        
        return sentences_per_batch
    
    def _extract_json_array(self, text: str) -> str:
        """Extract JSON array from response that might contain extra text"""
        import re
        
        # Look for JSON array pattern [...]
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            return match.group(0)
        
        # If no array found, return original (will likely fail JSON parsing)
        return text