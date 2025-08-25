import streamlit as st
from typing import List, Dict, Any

def show_content_percentages(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]):
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

def render_results(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    st.subheader("Classification Results")
    
    # Show percentages above the visualization
    show_content_percentages(sentences, results)
    
    # Legend
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <span style="background-color: lightblue; padding: 2px 6px; margin-right: 10px;">Info</span>
        <span style="background-color: lightcoral; padding: 2px 6px; margin-right: 10px;">Promo</span>
        <span style="background-color: lightgreen; padding: 2px 6px;">Risk</span>
    </div>
    """, unsafe_allow_html=True)
    
    html_content = ""
    color_map = {"info": "lightblue", "promo": "lightcoral", "risk": "lightgreen"}
    
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            sentence_html = ""
            for span in result["spans"]:
                text_part = sentence[span["start"]:span["end"]]
                color = color_map[span["label"]]
                sentence_html += f'<span style="background-color: {color};">{text_part}</span>'
        else:
            color = color_map[result["label"]]
            sentence_html = f'<span style="background-color: {color};">{sentence}</span>'
        
        html_content += f"{sentence_html} "
    
    st.markdown(html_content, unsafe_allow_html=True)

def generate_html_download(sentences: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    color_map = {"info": "lightblue", "promo": "lightcoral", "risk": "lightgreen"}
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Classification Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .legend { margin-bottom: 20px; }
        .legend span { padding: 2px 6px; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="legend">
        <span style="background-color: lightblue;">Info</span>
        <span style="background-color: lightcoral;">Promo</span>
        <span style="background-color: lightgreen;">Risk</span>
    </div>
    <div>"""
    
    for result in results:
        idx = result["idx"]
        sentence = sentences[idx]["content"]
        
        if "spans" in result:
            for span in result["spans"]:
                text_part = sentence[span["start"]:span["end"]]
                color = color_map[span["label"]]
                html_content += f'<span style="background-color: {color};">{text_part}</span>'
        else:
            color = color_map[result["label"]]
            html_content += f'<span style="background-color: {color};">{sentence}</span>'
        
        html_content += " "
    
    html_content += """</div></body></html>"""
    
    st.download_button(
        label="Download HTML",
        data=html_content,
        file_name="classification_results.html",
        mime="text/html"
    )
