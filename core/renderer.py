import html
from typing import List, Dict, Any
from core.classifier import ClassificationResult

class HTMLRenderer:
    """Renders classification results as color-coded HTML"""
    
    def __init__(self):
        self.css = """
<style>
:root{--info:#e7f0ff;--promo:#eaffea;--risk:#ffecec;--ink:#111;--muted:#555;--b:#e5e7eb}
body{font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto;color:var(--ink);max-width:none;margin:0;padding:1rem}
.info{background:var(--info);padding:0 .15em;border-radius:.15em}
.promo{background:var(--promo);padding:0 .15em;border-radius:.15em}
.risk{background:var(--risk);padding:0 .15em;border-radius:.15em}
.legend{font:14px/1.4 system-ui,-apple-system,Segoe UI,Roboto;color:var(--muted);margin:0 0 1.5rem 0;display:flex;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--b);padding-bottom:1rem}
.legend span{display:inline-flex;align-items:center;gap:.4rem}
.chip{width:1em;height:1em;border-radius:.2em;display:inline-block;box-shadow:inset 0 0 0 1px rgba(0,0,0,.05)}
.chip.info{background:var(--info)}.chip.promo{background:var(--promo)}.chip.risk{background:var(--risk)}
.content{line-height:1.8}
p{margin:0 0 1em 0}
h1,h2,h3,h4,h5,h6{margin:1.5em 0 .5em 0;color:var(--ink)}
ul,ol{margin:1em 0;padding-left:2em}
li{margin:.25em 0}
.stats{background:#f8f9fa;padding:1rem;border-radius:.5rem;margin:1rem 0;border:1px solid var(--b)}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-top:.5rem}
.stat-item{text-align:center}
.stat-number{font-size:1.5rem;font-weight:bold;margin-bottom:.25rem}
.stat-label{font-size:.875rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
</style>"""
        
        self.legend_html = """
<div class="legend">
  <span><i class="chip info"></i> Informational</span>
  <span><i class="chip promo"></i> Promotional</span>
  <span><i class="chip risk"></i> Risk warning</span>
</div>"""
    
    def render_classification_result(self, result: ClassificationResult) -> str:
        """
        Render the complete classification result as HTML
        Returns self-contained HTML document
        """
        # Generate statistics
        stats = result.get_statistics()
        stats_html = self._render_statistics(stats)
        
        # Render content with highlighting
        content_html = self._render_highlighted_content(result)
        
        # Combine everything
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Classification Results</title>
    {self.css}
</head>
<body>
    <h1>Content Classification Results</h1>
    {self.legend_html}
    {stats_html}
    <div class="content">
        {content_html}
    </div>
</body>
</html>"""
        
        return html_content
    
    def _render_statistics(self, stats: Dict[str, int]) -> str:
        """Render classification statistics"""
        total = sum(stats.values())
        
        return f"""
<div class="stats">
    <h3 style="margin-top:0">Classification Summary</h3>
    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-number" style="color:#0066cc">{stats.get('info_count', 0)}</div>
            <div class="stat-label">Informational</div>
        </div>
        <div class="stat-item">
            <div class="stat-number" style="color:#00aa44">{stats.get('promo_count', 0)}</div>
            <div class="stat-label">Promotional</div>
        </div>
        <div class="stat-item">
            <div class="stat-number" style="color:#cc4400">{stats.get('risk_count', 0)}</div>
            <div class="stat-label">Risk Warning</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{total}</div>
            <div class="stat-label">Total Items</div>
        </div>
    </div>
</div>"""
    
    def _render_highlighted_content(self, result: ClassificationResult) -> str:
        """Render the content with color-coded highlighting"""
        rendered_sentences = []
        
        for sentence in result.sentences:
            sentence_text = sentence['text']
            sentence_hash = sentence['hash']
            
            # Get classification for this sentence
            classification = result.get_sentence_classification(sentence_hash)
            
            if classification['type'] == 'phrase_level':
                # Render with phrase-level spans
                highlighted = self._render_phrase_level_sentence(sentence_text, classification['spans'])
            else:
                # Render with sentence-level label
                highlighted = self._render_sentence_level(sentence_text, classification['label'])
            
            rendered_sentences.append(highlighted)
        
        # Combine sentences into paragraphs (basic structure preservation)
        content = self._preserve_basic_structure(rendered_sentences)
        return content
    
    def _render_phrase_level_sentence(self, text: str, spans: List[Dict]) -> str:
        """Render a sentence with character-level spans"""
        if not spans:
            return html.escape(text)
        
        # Sort spans by start position
        sorted_spans = sorted(spans, key=lambda x: x['start'])
        
        result = ""
        for span in sorted_spans:
            start, end, label = span['start'], span['end'], span['label']
            span_text = text[start:end]
            escaped_text = html.escape(span_text)
            result += f'<span class="{label}">{escaped_text}</span>'
        
        return result
    
    def _render_sentence_level(self, text: str, label: str) -> str:
        """Render a sentence with single label"""
        escaped_text = html.escape(text)
        return f'<span class="{label}">{escaped_text}</span>'
    
    def _preserve_basic_structure(self, sentences: List[str]) -> str:
        """
        Basic structure preservation - group sentences into paragraphs
        This is a simple implementation that can be enhanced later
        """
        if not sentences:
            return ""
        
        # Simple paragraph detection: double newlines or very short sentences followed by longer ones
        paragraphs = []
        current_paragraph = []
        
        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)
            
            # Check if we should start a new paragraph
            # Simple heuristic: if sentence ends with double newline or is very short
            original_sentence = sentence.replace('<span class="info">', '').replace('<span class="promo">', '').replace('<span class="risk">', '').replace('</span>', '')
            
            should_break = (
                original_sentence.strip().endswith('\n\n') or
                (len(original_sentence.strip()) < 50 and i < len(sentences) - 1) or
                original_sentence.strip().startswith('#') or  # Headers
                original_sentence.strip().startswith('-') or  # Lists
                original_sentence.strip().startswith('*') or
                original_sentence.strip().startswith('•')
            )
            
            if should_break:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # Add remaining sentences
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Render paragraphs
        rendered_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Detect headers (lines starting with #)
                if paragraph.startswith('#'):
                    # Simple header detection
                    header_level = min(6, len(paragraph) - len(paragraph.lstrip('#')))
                    header_text = paragraph.lstrip('# ').strip()
                    rendered_paragraphs.append(f'<h{header_level}>{header_text}</h{header_level}>')
                # Detect list items
                elif paragraph.startswith(('-', '*', '•')):
                    rendered_paragraphs.append(f'<ul><li>{paragraph[1:].strip()}</li></ul>')
                else:
                    rendered_paragraphs.append(f'<p>{paragraph}</p>')
        
        return '\n'.join(rendered_paragraphs)
    
    def render_debug_json(self, result: ClassificationResult) -> str:
        """Render debug information as formatted JSON"""
        import json
        
        debug_data = {
            "sentences_count": len(result.sentences),
            "stage1_results_count": len(result.stage1_results),
            "stage2_results_count": len(result.stage2_results),
            "statistics": result.get_statistics(),
            "sentences": result.sentences[:5],  # First 5 for brevity
            "stage1_sample": result.stage1_results[:5],
            "stage2_sample": result.stage2_results[:3],
            "debug_info": result.debug_info
        }
        
        return json.dumps(debug_data, indent=2, ensure_ascii=False)