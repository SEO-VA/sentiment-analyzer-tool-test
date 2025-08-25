# core/renderer.py

import html
import json
from typing import List, Dict, Any

# Import the enhanced renderer that handles both text and webpage content
from core.structure_renderer import EnhancedHTMLRenderer

class HTMLRenderer:
    """Main renderer class - now uses enhanced renderer for backward compatibility"""
    
    def __init__(self):
        self.enhanced_renderer = EnhancedHTMLRenderer()
    
    def render_classification_result(self, result, webpage_data: Dict[str, Any] = None) -> str:
        """
        Render the complete classification result as HTML
        
        Args:
            result: Classification results from ContentClassifier
            webpage_data: Optional webpage structure data for web content
        
        Returns: Self-contained HTML document
        """
        return self.enhanced_renderer.render_classification_result(result, webpage_data)
    
    def render_debug_json(self, result) -> str:
        """Render debug information as formatted JSON"""
        
        debug_data = {
            "sentences_count": len(result.sentences) if hasattr(result, 'sentences') else 0,
            "stage1_results_count": len(result.stage1_results) if hasattr(result, 'stage1_results') else 0,
            "stage2_results_count": len(result.stage2_results) if hasattr(result, 'stage2_results') else 0,
            "statistics": result.get_statistics() if hasattr(result, 'get_statistics') else {},
            "sentences": (result.sentences[:5] if hasattr(result, 'sentences') and len(result.sentences) > 0 else []),
            "stage1_sample": (result.stage1_results[:5] if hasattr(result, 'stage1_results') and len(result.stage1_results) > 0 else []),
            "stage2_sample": (result.stage2_results[:3] if hasattr(result, 'stage2_results') and len(result.stage2_results) > 0 else []),
            "debug_info": result.debug_info if hasattr(result, 'debug_info') else {}
        }
        
        return json.dumps(debug_data, indent=2, ensure_ascii=False)