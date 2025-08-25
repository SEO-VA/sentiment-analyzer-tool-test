import json
import re
import openai
import streamlit as st
from typing import List, Dict, Any

def split_sentences(text: str) -> List[Dict[str, Any]]:
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Use simpler approach: split on sentence endings, then filter false positives
    sentences = re.split(r'[.!?]+\s*', text)
    
    # Filter out empty sentences and common abbreviations
    abbreviations = {'Mr', 'Ms', 'Mrs', 'Dr', 'Prof', 'Sr', 'Jr', 'vs', 'etc', 'i.e', 'e.g', 'U.S.A', 'U.K', 'U.N'}
    
    result = []
    idx = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Check if this looks like an abbreviation fragment
            words = sentence.split()
            if len(words) == 1 and words[0] in abbreviations:
                continue
            
            result.append({"idx": idx, "content": sentence})
            idx += 1
    
    return result

def call_openai_assistant(sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = openai.OpenAI(api_key=st.secrets["openai_api_key"])
    
    try:
        thread = client.beta.threads.create()
        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=json.dumps(sentences)
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=st.secrets["assistant_id"]
        )
        
        while run.status in ['queued', 'in_progress']:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return json.loads(messages.data[0].content[0].text.value)
        else:
            raise Exception(f"Run failed with status: {run.status}")
            
    except Exception as e:
        st.error(f"API call failed: {str(e)}")
        return []
