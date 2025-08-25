from typing import List, Dict, Any

def validate_response(response: List[Dict[str, Any]], sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    validated = []
    
    for i, item in enumerate(response):
        try:
            idx = item.get("idx", i)
            original_sentence = sentences[idx]["content"]
            
            if "spans" in item:
                spans = item["spans"]
                if validate_spans(spans, len(original_sentence)):
                    validated.append(item)
                else:
                    validated.append({"idx": idx, "label": "info"})
            elif "label" in item and item["label"] in ["info", "promo", "risk"]:
                validated.append(item)
            else:
                validated.append({"idx": idx, "label": "info"})
                
        except Exception:
            validated.append({"idx": i, "label": "info"})
    
    return validated

def validate_spans(spans: List[Dict[str, Any]], text_length: int) -> bool:
    if not spans:
        return False
    
    if spans[0]["start"] != 0 or spans[-1]["end"] != text_length:
        return False
    
    for i in range(len(spans) - 1):
        if spans[i]["end"] != spans[i + 1]["start"]:
            return False
    
    for span in spans:
        if span["label"] not in ["info", "promo", "risk"]:
            return False
    
    return True
