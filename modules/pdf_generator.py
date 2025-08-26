# modules/pdf_generator.py

from typing import List, Dict, Any, Optional
from io import BytesIO
import logging
import os
import sys

logger = logging.getLogger(__name__)

def generate_pdf_from_html(html_content: str) -> bytes:
    """
    Convert HTML content to PDF using available libraries
    Priority: WeasyPrint > ReportLab > raise exception
    
    Args:
        html_content: Complete HTML document as string
        
    Returns:
        PDF content as bytes
        
    Raises:
        Exception: If PDF generation fails or no libraries available
    """
    # Try WeasyPrint first (best quality)
    try:
        return _generate_pdf_weasyprint(html_content)
    except Exception as e:
        logger.warning(f"WeasyPrint failed: {str(e)}")
    
    # Fallback to ReportLab (simpler but works)
    try:
        return _generate_pdf_reportlab(html_content)
    except Exception as e:
        logger.warning(f"ReportLab failed: {str(e)}")
    
    # If all methods fail
    raise Exception(
        "PDF generation failed. No working PDF libraries available. "
        "This often happens on cloud platforms with missing system dependencies."
    )

def _generate_pdf_weasyprint(html_content: str) -> bytes:
    """Generate PDF using WeasyPrint (requires system dependencies)"""
    import weasyprint
    
    # Optimize HTML for PDF generation
    pdf_optimized_html = _optimize_html_for_pdf(html_content)
    
    # Generate PDF
    logger.info("Converting HTML to PDF using WeasyPrint")
    pdf_buffer = BytesIO()
    weasyprint.HTML(string=pdf_optimized_html).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    pdf_bytes = pdf_buffer.getvalue()
    logger.info(f"PDF generated successfully with WeasyPrint ({len(pdf_bytes)} bytes)")
    
    return pdf_bytes

def _generate_pdf_reportlab(html_content: str) -> bytes:
    """Generate PDF using ReportLab (pure Python, more reliable)"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    from bs4 import BeautifulSoup
    
    logger.info("Converting HTML to PDF using ReportLab")
    
    # Parse HTML to extract text content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    story = []
    
    # Extract title
    title_elem = soup.find('h1')
    if title_elem:
        title = Paragraph(title_elem.get_text().strip(), styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
    
    # Extract stats section
    stats_elem = soup.find(class_='stats')
    if stats_elem:
        stats_text = stats_elem.get_text(separator=' ', strip=True)
        stats_para = Paragraph(f"<b>Statistics:</b> {stats_text}", styles['Normal'])
        story.append(stats_para)
        story.append(Spacer(1, 12))
    
    # Extract source info
    source_elem = soup.find(class_='source-info')
    if source_elem:
        source_text = source_elem.get_text(separator=' ', strip=True)
        source_para = Paragraph(f"<b>Source:</b> {source_text}", styles['Normal'])
        story.append(source_para)
        story.append(Spacer(1, 12))
    
    # Extract main content (simplified - no background colors)
    content_elem = soup.find(class_='content')
    if content_elem:
        # Get text content and split into paragraphs
        text_content = content_elem.get_text(separator='\n', strip=True)
        paragraphs = text_content.split('\n')
        
        for para_text in paragraphs:
            para_text = para_text.strip()
            if para_text and len(para_text) > 10:  # Skip very short fragments
                para = Paragraph(para_text, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 6))
    
    # Add note about simplified formatting
    note = Paragraph(
        "<i>Note: This PDF was generated with simplified formatting. "
        "For full styling including color highlighting, please use the HTML version.</i>",
        styles['Italic']
    )
    story.append(Spacer(1, 12))
    story.append(note)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    pdf_bytes = buffer.getvalue()
    logger.info(f"PDF generated successfully with ReportLab ({len(pdf_bytes)} bytes)")
    
    return pdf_bytes

def _optimize_html_for_pdf(html_content: str) -> str:
    """
    Optimize HTML content for better PDF rendering
    
    Args:
        html_content: Original HTML content
        
    Returns:
        PDF-optimized HTML content
    """
    # Add PDF-specific CSS rules
    pdf_css_additions = '''
        @page { 
            size: A4; 
            margin: 2cm; 
        }
        
        body { 
            font-size: 12px; 
            color: #000; 
            background: white !important; 
        }
        
        /* Prevent page breaks inside important sections */
        .stats, .source-info, .legend { 
            page-break-inside: avoid; 
            break-after: avoid; 
        }
        
        /* Better handling of content breaks */
        .content { 
            page-break-inside: auto; 
        }
        
        /* Heading behavior */
        h1, h2, h3, h4, h5, h6 { 
            page-break-after: avoid; 
            page-break-inside: avoid;
        }
        
        /* Table handling */
        table { 
            page-break-inside: avoid; 
        }
        
        /* Ensure classification spans are visible in print */
        span[style*="background-color"] {
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }
        
        /* Fix margins for better PDF layout */
        .header {
            margin-bottom: 1.5cm;
        }
    '''
    
    # Insert PDF CSS after the opening <style> tag
    if '<style>' in html_content:
        html_content = html_content.replace(
            '<style>', 
            f'<style>{pdf_css_additions}'
        )
    else:
        # If no existing style tag, add one
        html_content = html_content.replace(
            '<head>',
            f'<head><style>{pdf_css_additions}</style>'
        )
    
    return html_content

def check_pdf_dependencies() -> Dict[str, Any]:
    """
    Check if PDF generation dependencies are available
    Tests actual functionality, not just imports
    
    Returns:
        Dict with dependency status and info
    """
    result = {
        'available': False,
        'methods': [],
        'primary_method': None,
        'missing_packages': [],
        'system_dependencies_missing': False,
        'error_message': None
    }
    
    # Test WeasyPrint
    weasyprint_works = False
    try:
        import weasyprint
        # Test actual functionality with a simple HTML
        test_html = "<html><body><p>Test</p></body></html>"
        test_buffer = BytesIO()
        weasyprint.HTML(string=test_html).write_pdf(test_buffer)
        weasyprint_works = True
        result['methods'].append('weasyprint')
        result['weasyprint_version'] = weasyprint.__version__
        logger.info("WeasyPrint is working correctly")
    except ImportError:
        result['missing_packages'].append('weasyprint')
    except Exception as e:
        # This is likely the system dependency issue
        result['system_dependencies_missing'] = True
        result['error_message'] = f"WeasyPrint system dependency error: {str(e)}"
        logger.warning(f"WeasyPrint available but not functional: {str(e)}")
    
    # Test ReportLab
    reportlab_works = False
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        # Test actual functionality
        test_buffer = BytesIO()
        test_canvas = canvas.Canvas(test_buffer, pagesize=letter)
        test_canvas.drawString(100, 750, "Test")
        test_canvas.save()
        reportlab_works = True
        result['methods'].append('reportlab')
        import reportlab
        result['reportlab_version'] = reportlab.Version
        logger.info("ReportLab is working correctly")
    except ImportError:
        result['missing_packages'].append('reportlab')
    except Exception as e:
        logger.warning(f"ReportLab available but not functional: {str(e)}")
    
    # Set availability and primary method
    if weasyprint_works:
        result['available'] = True
        result['primary_method'] = 'weasyprint'
    elif reportlab_works:
        result['available'] = True
        result['primary_method'] = 'reportlab'
    
    # Provide helpful error messages
    if not result['available']:
        if result['missing_packages']:
            result['error_message'] = f"Missing packages: {', '.join(result['missing_packages'])}"
        elif result['system_dependencies_missing']:
            result['error_message'] = (
                "PDF libraries are installed but missing system dependencies. "
                "This is common on cloud platforms like Streamlit Cloud."
            )
        else:
            result['error_message'] = "No working PDF generation methods available"
    
    return result

def estimate_pdf_size(html_content: str) -> Dict[str, Any]:
    """
    Estimate PDF characteristics without generating it
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        Dict with size estimates
    """
    # Simple heuristics for PDF size estimation
    html_length = len(html_content)
    estimated_pages = max(1, html_length // 5000)  # Rough estimate
    
    return {
        'html_size_chars': html_length,
        'estimated_pages': estimated_pages,
        'estimated_pdf_size_kb': estimated_pages * 50  # Rough estimate
    }