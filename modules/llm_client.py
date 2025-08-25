# modules/llm_client.py

import json
import time
import logging
from typing import List, Dict, Any

import openai
import streamlit as st

logger = logging.getLogger(__name__)

def call_openai_assistant(sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Call OpenAI assistant for content classification
    
    Args:
        sentences: List of {"idx": int, "content": str} dictionaries
        
    Returns:
        List of classification results with labels or spans
    """
    client = openai.OpenAI(api_key=st.secrets["openai_api_key"])
    
    try:
        logger.info(f"Classifying {len(sentences)} sentences with OpenAI assistant")
        
        # Create thread
        thread = client.beta.threads.create()
        
        # Send sentences as JSON
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=json.dumps(sentences, ensure_ascii=False)
        )
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=st.secrets["assistant_id"]
        )
        
        # Wait for completion
        max_wait_time = 60  # seconds
        start_time = time.time()
        
        while run.status in ['queued', 'in_progress']:
            if time.time() - start_time > max_wait_time:
                raise Exception("Assistant call timed out")
                
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id, 
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get the assistant's response
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            response_text = messages.data[0].content[0].text.value
            
            logger.info(f"Assistant response received: {len(response_text)} characters")
            logger.info(f"Response preview: {response_text[:200]}...")
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
                logger.info(f"Successfully parsed {len(result)} classification results")
                return result
                
            except json.JSONDecodeError as e:
                # Try to extract JSON from response that might have extra text
                logger.warning(f"JSON parsing failed, attempting extraction: {str(e)}")
                extracted_json = _extract_json_from_response(response_text)
                if extracted_json:
                    return json.loads(extracted_json)
                else:
                    raise Exception(f"Could not parse assistant response as JSON: {str(e)}")
                    
        elif run.status == 'failed':
            error_message = run.last_error.message if run.last_error else "Unknown error"
            raise Exception(f"Assistant run failed: {error_message}")
        else:
            raise Exception(f"Assistant run ended with unexpected status: {run.status}")
            
    except Exception as e:
        logger.error(f"OpenAI assistant call failed: {str(e)}")
        st.error(f"API call failed: {str(e)}")
        
        # Return fallback results so the app doesn't crash
        return _create_fallback_results(sentences)

def _extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON from response that might contain extra text
    Sometimes assistants add explanations around the JSON
    """
    import re
    
    # Look for JSON array pattern [...]
    array_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
    if array_match:
        return array_match.group(0)
    
    # Look for JSON object pattern {...}
    object_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
    if object_match:
        return object_match.group(0)
    
    return None

def _create_fallback_results(sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create fallback results when assistant call fails
    All sentences default to 'info' classification
    """
    logger.info("Creating fallback results (all sentences marked as 'info')")
    
    fallback_results = []
    for sentence in sentences:
        fallback_results.append({
            "idx": sentence["idx"],
            "label": "info"  # Safe default
        })
    
    return fallback_results

def estimate_api_cost(sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Estimate API usage for planning purposes
    
    Returns:
        Dict with token estimates and approximate cost
    """
    # Rough token estimation (4 characters ≈ 1 token)
    total_chars = sum(len(s["content"]) for s in sentences)
    estimated_input_tokens = total_chars // 4
    
    # Assistant responses are typically shorter
    estimated_output_tokens = estimated_input_tokens // 2
    
    return {
        "sentences": len(sentences),
        "total_characters": total_chars,
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens
    }