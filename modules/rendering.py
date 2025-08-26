# modules/rendering.py

import html
import streamlit as st
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag, NavigableString
from modules.google_docs_generator import generate_google_docs_files, get_google_docs_import_instructions

def show_content_percentages(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    """Calculate and display content breakdown percentages"""
    # Calculate character counts per category
    char_counts = {"info": 0, "promo": 0, "risk": 0}
    
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            for span in result["spans"]:
                char_count = span["end"] - span["start"]
                char_counts[span["label"]] += char_count
        else:
            char_counts[result["label"]] += len(sentence)
    
    total_chars = sum(char_counts.values())
    
    if total_chars > 0:
        info_pct = round((char_counts["info"] / total_chars) * 100, 1)
        promo_pct = round((char_counts["promo"] / total_chars) * 100, 1)
        risk_pct = round((char_counts["risk"] / total_chars) * 100, 1)
        
        st.markdown(f"""
        <div style="margin-bottom: 20px; padding: 10px; border-radius: 5px; background-color: #f0f0f0;">
            <strong>Content Breakdown:</strong> 
            <span style="background-color: lightblue; padding: 2px 6px; margin-left: 10px;">Info: {info_pct}%</span>
            <span style="background-color: lightcoral; padding: 2px 6px; margin-left: 10px;">Promo: {promo_pct}%</span>
            <span style="background-color: lightgreen; padding: 2px 6px; margin-left: 10px;">Risk: {risk_pct}%</span>
        </div>
        """, unsafe_allow_html=True)

def render_results(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]], 
                  webpage_data: Optional[Dict[str, Any]] = None):
    """
    Render classification results with appropriate formatting
    
    Args:
        sentences: List of sentence data
        results: Classification results
        webpage_data: Optional webpage structure data for enhanced rendering
    """
    st.subheader("Classification Results")
    
    # Show percentages above the visualization
    show_content_percentages(sentences, results)
    
    # Show legend
    _show_legend()
    
    if webpage_data and webpage_data.get('success'):
        # Render with webpage structure preservation
        html_content = _render_webpage_structure(sentences, results, webpage_data)
    else:
        # Render with simple text highlighting
        html_content = _render_simple_text(sentences, results)
    
    # Display the rendered content
    st.markdown(html_content, unsafe_allow_html=True)

def generate_html_download(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]], 
                          webpage_data: Optional[Dict[str, Any]] = None):
    """
    Generate downloadable files with classification results
    Focus on HTML and Google Docs import formats
    """
    if webpage_data and webpage_data.get('success'):
        # Generate webpage-style HTML
        html_content = _generate_webpage_html(sentences, results, webpage_data)
        filename_base = f"webpage_classification_{webpage_data.get('title', 'results')}"
    else:
        # Generate simple HTML
        html_content = _generate_simple_html(sentences, results)
        filename_base = "text_classification_results"
    
    # Clean filename
    import re
    filename_base = re.sub(r'[^\w\s-]', '', filename_base)
    filename_base = re.sub(r'[-\s]+', '-', filename_base)
    
    # Show download options
    st.subheader("Download Options")
    
    # Create tabs for different download types
    tab1, tab2 = st.tabs(["📄 Standard HTML", "📝 Google Docs Import"])
    
    with tab1:
        # Standard HTML download
        st.markdown("### 🌐 HTML Download")
        st.markdown("Standard HTML file with full color highlighting - works in any browser.")
        
        st.download_button(
            label="📄 Download HTML",
            data=html_content,
            file_name=f"{filename_base}.html",
            mime="text/html",
            help="HTML file with full color highlighting and formatting"
        )
        
        st.info("💡 **Tip:** Open the HTML file in any browser and use 'Print to PDF' for a PDF version.")
    
    with tab2:
        # Google Docs optimized downloads
        st.markdown("### 🎯 Perfect for Google Docs Import")
        st.markdown("These formats preserve **all colors and formatting** when imported to Google Docs!")
        
        try:
            # Generate Google Docs files
            with st.spinner("Generating Google Docs files..."):
                google_files = generate_google_docs_files(sentences, results, webpage_data)
            
            # Create download columns based on available formats
            cols = st.columns(len(google_files))
            
            for i, (format_name, file_content) in enumerate(google_files.items()):
                with cols[i]:
                    format_labels = {
                        'rtf': '📝 RTF (Best Colors)',
                        'html': '🌐 HTML (Google Optimized)', 
                        'docx': '📄 Word Document'
                    }
                    
                    format_help = {
                        'rtf': 'Rich Text Format - preserves colors perfectly in Google Docs',
                        'html': 'HTML optimized for Google Docs import',
                        'docx': 'Microsoft Word format with highlighting'
                    }
                    
                    label = format_labels.get(format_name, format_name.upper())
                    help_text = format_help.get(format_name, f'{format_name.upper()} format')
                    
                    st.download_button(
                        label=label,
                        data=file_content,
                        file_name=f"{filename_base}.{format_name}",
                        mime=_get_mime_type(format_name),
                        help=help_text
                    )
            
            # Show import instructions
            with st.expander("📋 How to Import to Google Docs", expanded=False):
                instructions = get_google_docs_import_instructions()
                st.markdown(instructions)
                
                # Add visual guide
                st.markdown("### 🎨 What You'll Get:")
                st.markdown("""
                - ✅ **Perfect color preservation** - All highlighting maintained
                - ✅ **Professional formatting** - Statistics, legends, proper layout  
                - ✅ **Editable in Google Docs** - Modify, share, collaborate normally
                - ✅ **High-quality PDF export** - Use Google Docs' Print to PDF
                """)
                
            # Success message
            st.success("✨ **Recommended:** Download RTF format for best results in Google Docs!")
                
        except Exception as e:
            st.error(f"Google Docs file generation failed: {str(e)}")
            st.info("Standard HTML download is still available in the other tab.")

def _get_mime_type(format_name: str) -> str:
    """Get MIME type for file format"""
    mime_types = {
        'rtf': 'application/rtf',
        'html': 'text/html',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    return mime_types.get(format_name, 'application/octet-stream')

def _show_legend():
    """Display color legend"""
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <span style="background-color: lightblue; padding: 2px 6px; margin-right: 10px;">Info</span>
        <span style="background-color: lightcoral; padding: 2px 6px; margin-right: 10px;">Promo</span>
        <span style="background-color: lightgreen; padding: 2px 6px;">Risk</span>
    </div>
    """, unsafe_allow_html=True)

def _render_simple_text(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> str:
    """Render classification results as simple highlighted text"""
    html_content = ""
    color_map = {"info": "lightblue", "promo": "lightcoral", "risk": "lightgreen"}
    
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            # Render with phrase-level spans
            sentence_html = ""
            for span in result["spans"]:
                text_part = sentence[span["start"]:span["end"]]
                color = color_map[span["label"]]
                escaped_text = html.escape(text_part)
                sentence_html += f'<span style="background-color: {color};">{escaped_text}</span>'
        else:
            # Render with sentence-level classification
            color = color_map[result["label"]]
            escaped_text = html.escape(sentence)
            sentence_html = f'<span style="background-color: {color};">{escaped_text}</span>'
        
        html_content += f"{sentence_html} "
    
    return html_content

def _render_webpage_structure(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]], 
                             webpage_data: Dict[str, Any]) -> str:
    """Render classification results preserving webpage structure"""
    structure_html = webpage_data.get('structure', '')
    if not structure_html:
        # Fallback to simple rendering
        return _render_simple_text(sentences, results)
    
    # Parse the preserved structure
    soup = BeautifulSoup(structure_html, 'html.parser')
    
    # Build classification lookup
    classification_map = _build_classification_map(sentences, results)
    
    # Apply classifications to the DOM structure
    _apply_classifications_to_dom(soup, classification_map)
    
    return str(soup)

def _build_classification_map(sentences: List[Dict[str, Any]], 
                            results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a lookup map for applying classifications"""
    classification_map = {}
    
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        # Store both the original text and its classification
        classification_map[sentence] = result
        classification_map[sentence.lower()] = result
        
        # Also store sentence fragments for partial matching
        if len(sentence) > 50:
            words = sentence.split()
            if len(words) > 3:
                # Create fragment keys for better matching
                start_fragment = ' '.join(words[:3])
                end_fragment = ' '.join(words[-3:])
                classification_map[start_fragment] = result
                classification_map[end_fragment] = result
    
    return classification_map

def _apply_classifications_to_dom(element, classification_map: Dict[str, Any]):
    """Walk through DOM elements and apply classifications"""
    color_map = {"info": "lightblue", "promo": "lightcoral", "risk": "lightgreen"}
    
    if isinstance(element, NavigableString):
        return
    
    # Process text nodes
    for child in list(element.children):
        if isinstance(child, NavigableString):
            text_content = str(child).strip()
            if text_content and len(text_content) > 10:  # Only process substantial text
                # Try to find classification for this text
                result = _find_text_classification(text_content, classification_map)
                
                if result:
                    # Apply classification
                    if "spans" in result:
                        # Use phrase-level classification
                        classified_html = _apply_spans_to_text(text_content, result["spans"], color_map)
                    else:
                        # Use sentence-level classification
                        color = color_map.get(result["label"], "lightgray")
                        escaped_text = html.escape(text_content)
                        classified_html = f'<span style="background-color: {color};">{escaped_text}</span>'
                    
                    # Replace text with classified version
                    new_soup = BeautifulSoup(classified_html, 'html.parser')
                    child.replace_with(new_soup)
        else:
            # Recursively process child elements
            _apply_classifications_to_dom(child, classification_map)

def _find_text_classification(text: str, classification_map: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find the best classification match for a piece of text"""
    # Try exact match first
    result = classification_map.get(text) or classification_map.get(text.lower())
    if result:
        return result
    
    # Try partial matching for longer texts
    if len(text) > 30:
        words = text.lower().split()
        if len(words) > 3:
            # Try matching start and end fragments
            start_fragment = ' '.join(words[:3])
            end_fragment = ' '.join(words[-3:])
            
            result = classification_map.get(start_fragment) or classification_map.get(end_fragment)
            if result:
                return result
    
    # Try substring matching (less precise but catches more cases)
    text_lower = text.lower()
    for key, result in classification_map.items():
        if isinstance(key, str) and len(key) > 20:
            if key.lower() in text_lower or text_lower in key.lower():
                return result
    
    return None

def _apply_spans_to_text(text: str, spans: List[Dict[str, Any]], 
                        color_map: Dict[str, str]) -> str:
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
        color = color_map.get(label, "lightgray")
        escaped_text = html.escape(span_text)
        result_html += f'<span style="background-color: {color};">{escaped_text}</span>'
    
    return result_html if result_html else html.escape(text)

def _generate_simple_html(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> str:
    """Generate simple HTML download with percentages included"""
    color_map = {"info": "lightblue", "promo": "lightcoral", "risk": "lightgreen"}
    
    # Calculate percentages
    char_counts = {"info": 0, "promo": 0, "risk": 0}
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            for span in result["spans"]:
                char_count = span["end"] - span["start"]
                char_counts[span["label"]] += char_count
        else:
            char_counts[result["label"]] += len(sentence)
    
    total_chars = sum(char_counts.values())
    info_pct = round((char_counts["info"] / total_chars) * 100, 1) if total_chars > 0 else 0
    promo_pct = round((char_counts["promo"] / total_chars) * 100, 1) if total_chars > 0 else 0
    risk_pct = round((char_counts["risk"] / total_chars) * 100, 1) if total_chars > 0 else 0
    
    # Build the HTML content with string formatting
    html_parts = []
    
    # HTML header
    html_parts.append("""<!DOCTYPE html>
<html>
<head>
    <title>Classification Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .stats { 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
        }
        .stats h3 { margin-top: 0; margin-bottom: 15px; }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
        }
        .stat-item { text-align: center; }
        .stat-number { font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.875rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
        .legend { margin-bottom: 20px; }
        .legend span { padding: 2px 6px; margin-right: 10px; border-radius: 3px; }
        .content { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Content Classification Results</h1>
    
    <div class="stats">
        <h3>Classification Summary</h3>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number" style="color:#0066cc">""")
    
    # Add statistics
    html_parts.append(str(char_counts["info"]))
    html_parts.append(f"""</div>
                <div class="stat-label">Informational ({info_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color:#00aa44">""")
    html_parts.append(str(char_counts["promo"]))
    html_parts.append(f"""</div>
                <div class="stat-label">Promotional ({promo_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color:#cc4400">""")
    html_parts.append(str(char_counts["risk"]))
    html_parts.append(f"""</div>
                <div class="stat-label">Risk Warning ({risk_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">""")
    html_parts.append(str(len(results)))
    html_parts.append("""</div>
                <div class="stat-label">Total Items</div>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <strong>Legend:</strong>
        <span style="background-color: lightblue;">Info</span>
        <span style="background-color: lightcoral;">Promo</span>
        <span style="background-color: lightgreen;">Risk</span>
    </div>
    <div class="content">""")
    
    # Add classified content
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            for span in result["spans"]:
                text_part = sentence[span["start"]:span["end"]]
                color = color_map[span["label"]]
                escaped_text = html.escape(text_part)
                html_parts.append(f'<span style="background-color: {color};">{escaped_text}</span>')
        else:
            color = color_map[result["label"]]
            escaped_text = html.escape(sentence)
            html_parts.append(f'<span style="background-color: {color};">{escaped_text}</span>')
        
        html_parts.append(" ")
    
    # Close HTML
    html_parts.append("</div></body></html>")
    
    return ''.join(html_parts)

def _generate_webpage_html(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]], 
                          webpage_data: Dict[str, Any]) -> str:
    """Generate webpage-style HTML download with enhanced styling and percentages"""
    title = webpage_data.get('title', 'Classification Results')
    url = webpage_data.get('url', '')
    
    # Calculate percentages
    char_counts = {"info": 0, "promo": 0, "risk": 0}
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            for span in result["spans"]:
                char_count = span["end"] - span["start"]
                char_counts[span["label"]] += char_count
        else:
            char_counts[result["label"]] += len(sentence)
    
    total_chars = sum(char_counts.values())
    info_pct = round((char_counts["info"] / total_chars) * 100, 1) if total_chars > 0 else 0
    promo_pct = round((char_counts["promo"] / total_chars) * 100, 1) if total_chars > 0 else 0
    risk_pct = round((char_counts["risk"] / total_chars) * 100, 1) if total_chars > 0 else 0
    
    # Get classified content
    content_html = _render_webpage_structure(sentences, results, webpage_data)
    
    # Build HTML using string concatenation to avoid formatting conflicts
    html_parts = []
    
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
    <title>Content Classification: {html.escape(title)}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            line-height: 1.6; 
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{ 
            border-bottom: 2px solid #ccc; 
            padding-bottom: 20px; 
            margin-bottom: 20px; 
        }}
        .source-info {{ 
            background-color: #f0f9ff; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px;
            border-left: 4px solid #0369a1;
        }}
        .stats {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
        }}
        .stats h3 {{ margin-top: 0; margin-bottom: 15px; }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
        }}
        .stat-item {{ text-align: center; }}
        .stat-number {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 0.875rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }}
        .legend {{ 
            margin-bottom: 20px; 
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .legend span {{ 
            padding: 4px 8px; 
            margin-right: 15px; 
            border-radius: 3px;
            font-weight: bold;
        }}
        .content {{ 
            margin-top: 20px; 
            background-color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        h1, h2, h3, h4, h5, h6 {{ margin-top: 1.5em; margin-bottom: 0.5em; }}
        p {{ margin-bottom: 1em; }}
        ul, ol {{ margin: 1em 0; padding-left: 2em; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Content Classification Results</h1>
        <div class="source-info">
            <h3>Source Page</h3>
            <p><strong>Title:</strong> {html.escape(title)}</p>""")
    
    if url:
        html_parts.append(f'<p><strong>URL:</strong> <a href="{html.escape(url)}" target="_blank">{html.escape(url)}</a></p>')
    
    html_parts.append(f"""
        </div>
    </div>
    
    <div class="stats">
        <h3>Classification Summary</h3>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-number" style="color:#0066cc">{char_counts["info"]}</div>
                <div class="stat-label">Informational ({info_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color:#00aa44">{char_counts["promo"]}</div>
                <div class="stat-label">Promotional ({promo_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" style="color:#cc4400">{char_counts["risk"]}</div>
                <div class="stat-label">Risk Warning ({risk_pct}%)</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(results)}</div>
                <div class="stat-label">Total Items</div>
            </div>
        </div>
    </div>
    
    <div class="legend">
        <strong>Classification Legend:</strong>
        <span style="background-color: lightblue;">Informational</span>
        <span style="background-color: lightcoral;">Promotional</span>
        <span style="background-color: lightgreen;">Risk Warning</span>
    </div>
    
    <div class="content">
        {content_html}
    </div>
</body>
</html>""")
    
    return ''.join(html_parts)