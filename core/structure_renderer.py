# core/structure_renderer.py

import html
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag, NavigableString

class WebpageRenderer:
    """Renders classification results preserving original webpage structure"""
    
    def __init__(self):
        self.css = """
<style>
:root {
    --info: #e7f0ff;
    --promo: #eaffea; 
    --risk: #ffecec;
    --ink: #111;
    --muted: #555;
    --border: #e5e7eb;
}

body {
    font: 16px/1.6 system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: var(--ink);
    max-width: none;
    margin: 0;
    padding: 1rem;
    background: #fff;
}

/* Classification highlighting */
.classified-content .info {
    background: var(--info);
    padding: 0 0.15em;
    border-radius: 0.15em;
}

.classified-content .promo {
    background: var(--promo);
    padding: 0 0.15em;
    border-radius: 0.15em;
}

.classified-content .risk {
    background: var(--risk);
    padding: 0 0.15em;
    border-radius: 0.15em;
}

/* Preserve original structure styling */
.classified-content h1, 
.classified-content h2, 
.classified-content h3, 
.classified-content h4, 
.classified-content h5, 
.classified-content h6 {
    margin: 1.5em 0 0.5em 0;
    color: var(--ink);
    line-height: 1.2;
}

.classified-content h1 { font-size: 2rem; font-weight: bold; }
.classified-content h2 { font-size: 1.5rem; font-weight: bold; }
.classified-content h3 { font-size: 1.25rem; font-weight: bold; }
.classified-content h4 { font-size: 1.1rem; font-weight: bold; }
.classified-content h5 { font-size: 1rem; font-weight: bold; }
.classified-content h6 { font-size: 0.9rem; font-weight: bold; }

.classified-content p {
    margin: 0 0 1em 0;
    line-height: 1.6;
}

.classified-content ul, 
.classified-content ol {
    margin: 1em 0;
    padding-left: 2em;
}

.classified-content li {
    margin: 0.25em 0;
    line-height: 1.5;
}

.classified-content table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    border: 1px solid var(--border);
}

.classified-content th, 
.classified-content td {
    border: 1px solid var(--border);
    padding: 0.5em;
    text-align: left;
    vertical-align: top;
}

.classified-content th {
    background: #f8f9fa;
    font-weight: bold;
}

.classified-content blockquote {
    border-left: 4px solid var(--border);
    margin: 1em 0;
    padding: 0 0 0 1em;
    color: var(--muted);
}

/* Legend */
.legend {
    font: 14px/1.4 system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: var(--muted);
    margin: 0 0 1.5rem 0;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
}

.legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.chip {
    width: 1em;
    height: 1em;
    border-radius: 0.2em;
    display: inline-block;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05);
}

.chip.info { background: var(--info); }
.chip.promo { background: var(--promo); }
.chip.risk { background: var(--risk); }

/* Statistics */
.stats {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
    border: 1px solid var(--border);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 0.25rem;
}

.stat-label {
    font-size: 0.875rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Source info */
.source-info {
    background: #f0f9ff;
    border: 1px solid #0369a1;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 1rem 0;
}

.source-info h3 {
    margin: 0 0 0.5rem 0;
    color: #0369a1;
}

.source-url {
    font-family: monospace;
    background: rgba(0,0,0,0.05);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    word-break: break-all;
}
</style>"""
        
        self.legend_html = """
<div class="legend">
  <span><i class="chip info"></i> Informational</span>
  <span><i class="chip promo"></i> Promotional</span>
  <span><i class="chip risk"></i> Risk warning</span>
</div>"""
    
    def render_webpage_result(self, result, webpage_data: Dict[str, Any]) -> str:
        """
        Render classification results preserving webpage structure
        
        Args:
            result: ClassificationResult from classifier
            webpage_data: Dict with 'structure', 'title', 'url', etc.
        """
        # Extract webpage info
        title = webpage_data.get('title', 'Classified Content')
        url = webpage_data.get('url', '')
        structure_html = webpage_data.get('structure', {}).get('html', '')
        
        # Generate statistics
        stats = result.get_statistics()
        stats_html = self._render_statistics(stats)
        
        # Source information
        source_html = self._render_source_info(title, url)
        
        # Reconstruct content with classifications
        classified_content = self._reconstruct_with_classifications(
            structure_html, result
        )
        
        # Combine everything
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Classification: {html.escape(title)}</title>
    {self.css}
</head>
<body>
    <h1>Content Classification Results</h1>
    {source_html}
    {self.legend_html}
    {stats_html}
    <div class="classified-content">
        {classified_content}
    </div>
</body>
</html>"""
        
        return html_content
    
    def _render_source_info(self, title: str, url: str) -> str:
        """Render source page information"""
        return f"""
<div class="source-info">
    <h3>Source Page</h3>
    <p><strong>Title:</strong> {html.escape(title)}</p>
    {f'<p><strong>URL:</strong> <span class="source-url">{html.escape(url)}</span></p>' if url else ''}
</div>"""
    
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
    
    def _reconstruct_with_classifications(self, structure_html: str, result) -> str:
        """
        Reconstruct HTML structure with classification highlighting
        
        This is the core function that maps AI classifications back onto 
        the original webpage structure.
        """
        if not structure_html:
            # Fallback to basic rendering if no structure
            return self._render_basic_classification(result)
        
        # Parse the preserved structure
        soup = BeautifulSoup(structure_html, 'lxml')
        main_element = soup.find() or soup
        
        # Build text-to-sentence mapping
        text_map = self._build_text_mapping(result.sentences)
        
        # Walk through the DOM and apply classifications
        self._apply_classifications_to_dom(main_element, text_map, result)
        
        return str(main_element)
    
    def _build_text_mapping(self, sentences: List[Dict]) -> Dict[str, Dict]:
        """
        Build mapping from text content to sentence data
        This helps us find which sentence a piece of text belongs to
        """
        text_map = {}
        
        for sentence in sentences:
            text = sentence['text'].strip()
            # Create multiple mapping keys for flexible matching
            text_map[text] = sentence
            text_map[text.lower()] = sentence
            
            # Also map significant phrases (for partial matching)
            if len(text) > 50:
                words = text.split()
                if len(words) > 5:
                    # Create key from first and last few words
                    key_start = ' '.join(words[:3])
                    key_end = ' '.join(words[-3:])
                    text_map[f"{key_start}...{key_end}"] = sentence
        
        return text_map
    
    def _apply_classifications_to_dom(self, element: Tag, text_map: Dict, result):
        """
        Walk through DOM elements and apply classifications
        """
        if isinstance(element, NavigableString):
            return
        
        # Process text nodes and apply classifications
        for child in list(element.children):
            if isinstance(child, NavigableString):
                # This is a text node - check if it matches any classified sentences
                text_content = str(child).strip()
                if text_content:
                    classified_html = self._classify_text_content(
                        text_content, text_map, result
                    )
                    if classified_html != html.escape(text_content):
                        # Replace text with classified version
                        new_soup = BeautifulSoup(classified_html, 'html.parser')
                        child.replace_with(new_soup)
            else:
                # Recursively process child elements
                self._apply_classifications_to_dom(child, text_map, result)
    
    def _classify_text_content(self, text: str, text_map: Dict, result) -> str:
        """
        Apply classifications to a piece of text content
        
        This function tries to match the text against classified sentences
        and applies appropriate highlighting.
        """
        text = text.strip()
        if not text:
            return text
        
        # Try exact match first
        sentence_data = text_map.get(text) or text_map.get(text.lower())
        
        if sentence_data:
            # Found exact match
            return self._apply_sentence_classification(text, sentence_data, result)
        
        # Try partial matching for longer texts
        if len(text) > 20:
            best_match = self._find_best_sentence_match(text, result.sentences)
            if best_match:
                return self._apply_sentence_classification(text, best_match, result)
        
        # Try to find if this text is part of a larger classified sentence
        containing_sentence = self._find_containing_sentence(text, result.sentences)
        if containing_sentence:
            return self._apply_partial_classification(text, containing_sentence, result)
        
        # No classification found, return escaped original text
        return html.escape(text)
    
    def _find_best_sentence_match(self, text: str, sentences: List[Dict]):
        """Find the sentence that best matches the given text"""
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for sentence in sentences:
            sentence_text = sentence['text'].lower()
            
            # Calculate similarity score (simple overlap-based)
            text_words = set(text_lower.split())
            sentence_words = set(sentence_text.split())
            overlap = len(text_words & sentence_words)
            total_words = len(text_words | sentence_words)
            
            if total_words > 0:
                score = overlap / total_words
                if score > best_score and score > 0.7:  # 70% similarity threshold
                    best_score = score
                    best_match = sentence
        
        return best_match
    
    def _find_containing_sentence(self, text: str, sentences: List[Dict]):
        """Find if text is contained within a classified sentence"""
        text_lower = text.lower()
        
        for sentence in sentences:
            sentence_text = sentence['text'].lower()
            if text_lower in sentence_text or sentence_text in text_lower:
                return sentence
        
        return None
    
    def _apply_sentence_classification(self, text: str, sentence_data: Dict, result) -> str:
        """Apply classification to a matched sentence"""
        sentence_hash = sentence_data['hash']
        classification = result.get_sentence_classification(sentence_hash)
        
        if classification['type'] == 'phrase_level':
            # Apply phrase-level classifications
            return self._apply_phrase_level_classification(text, classification['spans'])
        else:
            # Apply sentence-level classification
            label = classification['label']
            escaped_text = html.escape(text)
            return f'<span class="{label}">{escaped_text}</span>'
    
    def _apply_partial_classification(self, text: str, sentence_data: Dict, result) -> str:
        """Apply classification when text is part of a larger sentence"""
        sentence_hash = sentence_data['hash']
        classification = result.get_sentence_classification(sentence_hash)
        
        # For partial matches, we apply sentence-level classification
        # (phrase-level would be too complex to map accurately)
        label = classification.get('label', 'info')
        escaped_text = html.escape(text)
        return f'<span class="{label}">{escaped_text}</span>'
    
    def _apply_phrase_level_classification(self, text: str, spans: List[Dict]) -> str:
        """Apply phrase-level span classifications to text"""
        if not spans:
            return html.escape(text)
        
        # Sort spans by start position
        sorted_spans = sorted(spans, key=lambda x: x['start'])
        
        result_html = ""
        for span in sorted_spans:
            start, end, label = span['start'], span['end'], span['label']
            
            # Ensure bounds are valid for current text
            if start >= len(text) or end > len(text) or start >= end:
                continue
                
            span_text = text[start:end]
            escaped_text = html.escape(span_text)
            result_html += f'<span class="{label}">{escaped_text}</span>'
        
        return result_html if result_html else html.escape(text)
    
    def _render_basic_classification(self, result) -> str:
        """Fallback rendering when no webpage structure is available"""
        rendered_sentences = []
        
        for sentence in result.sentences:
            sentence_text = sentence['text']
            sentence_hash = sentence['hash']
            
            classification = result.get_sentence_classification(sentence_hash)
            
            if classification['type'] == 'phrase_level':
                highlighted = self._apply_phrase_level_classification(
                    sentence_text, classification['spans']
                )
            else:
                label = classification['label']
                escaped_text = html.escape(sentence_text)
                highlighted = f'<span class="{label}">{escaped_text}</span>'
            
            rendered_sentences.append(highlighted)
        
        # Basic paragraph structure
        paragraphs = []
        current_paragraph = []
        
        for sentence in rendered_sentences:
            current_paragraph.append(sentence)
            
            # Simple paragraph break logic
            if len(current_paragraph) >= 3:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Render as paragraphs
        html_paragraphs = [f'<p>{p}</p>' for p in paragraphs if p.strip()]
        return '\n'.join(html_paragraphs)


class EnhancedHTMLRenderer:
    """Enhanced version of the original renderer that can handle both text and webpage content"""
    
    def __init__(self):
        self.webpage_renderer = WebpageRenderer()
        
        # Original CSS for text-only content
        self.original_css = """
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
        
        self.original_legend = """
<div class="legend">
  <span><i class="chip info"></i> Informational</span>
  <span><i class="chip promo"></i> Promotional</span>
  <span><i class="chip risk"></i> Risk warning</span>
</div>"""
    
    def render_classification_result(self, result, webpage_data: Dict[str, Any] = None) -> str:
        """
        Unified rendering method that handles both text and webpage content
        
        Args:
            result: ClassificationResult from classifier
            webpage_data: Optional webpage data for structure preservation
        """
        if webpage_data and webpage_data.get('success', False):
            # Use webpage structure renderer
            return self.webpage_renderer.render_webpage_result(result, webpage_data)
        else:
            # Use original text-only renderer
            return self._render_text_only_result(result)
    
    def _render_text_only_result(self, result) -> str:
        """Original text-only rendering (maintains compatibility)"""
        # Generate statistics
        stats = result.get_statistics()
        stats_html = self._render_original_statistics(stats)
        
        # Render content with highlighting
        content_html = self._render_original_highlighted_content(result)
        
        # Combine everything
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Classification Results</title>
    {self.original_css}
</head>
<body>
    <h1>Content Classification Results</h1>
    {self.original_legend}
    {stats_html}
    <div class="content">
        {content_html}
    </div>
</body>
</html>"""
        
        return html_content
    
    def _render_original_statistics(self, stats: Dict[str, int]) -> str:
        """Original statistics rendering"""
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
    
    def _render_original_highlighted_content(self, result) -> str:
        """Original content highlighting (maintains compatibility)"""
        rendered_sentences = []
        
        for sentence in result.sentences:
            sentence_text = sentence['text']
            sentence_hash = sentence['hash']
            
            classification = result.get_sentence_classification(sentence_hash)
            
            if classification['type'] == 'phrase_level':
                highlighted = self._render_original_phrase_level(sentence_text, classification['spans'])
            else:
                highlighted = self._render_original_sentence_level(sentence_text, classification['label'])
            
            rendered_sentences.append(highlighted)
        
        # Basic structure preservation
        content = self._preserve_original_basic_structure(rendered_sentences)
        return content
    
    def _render_original_phrase_level(self, text: str, spans: List[Dict]) -> str:
        """Original phrase-level rendering"""
        if not spans:
            return html.escape(text)
        
        sorted_spans = sorted(spans, key=lambda x: x['start'])
        
        result_html = ""
        for span in sorted_spans:
            start, end, label = span['start'], span['end'], span['label']
            span_text = text[start:end]
            escaped_text = html.escape(span_text)
            result_html += f'<span class="{label}">{escaped_text}</span>'
        
        return result_html
    
    def _render_original_sentence_level(self, text: str, label: str) -> str:
        """Original sentence-level rendering"""
        escaped_text = html.escape(text)
        return f'<span class="{label}">{escaped_text}</span>'
    
    def _preserve_original_basic_structure(self, sentences: List[str]) -> str:
        """Original basic structure preservation"""
        if not sentences:
            return ""
        
        paragraphs = []
        current_paragraph = []
        
        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)
            
            original_sentence = re.sub(r'<span class="[^"]*">|</span>', '', sentence)
            
            should_break = (
                original_sentence.strip().endswith('\n\n') or
                (len(original_sentence.strip()) < 50 and i < len(sentences) - 1) or
                original_sentence.strip().startswith('#') or
                original_sentence.strip().startswith('-') or
                original_sentence.strip().startswith('*') or
                original_sentence.strip().startswith('•')
            )
            
            if should_break:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        rendered_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                if paragraph.startswith('#'):
                    header_level = min(6, len(paragraph) - len(paragraph.lstrip('#')))
                    header_text = paragraph.lstrip('# ').strip()
                    rendered_paragraphs.append(f'<h{header_level}>{header_text}</h{header_level}>')
                elif paragraph.startswith(('-', '*', '•')):
                    rendered_paragraphs.append(f'<ul><li>{paragraph[1:].strip()}</li></ul>')
                else:
                    rendered_paragraphs.append(f'<p>{paragraph}</p>')
        
        return '\n'.join(rendered_paragraphs)