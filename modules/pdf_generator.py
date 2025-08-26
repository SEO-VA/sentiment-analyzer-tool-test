# modules/pdf_generator.py

from typing import List, Dict, Any, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def generate_pdf_from_html(html_content: str) -> bytes:
    """
    Convert HTML content to PDF using weasyprint
    
    Args:
        html_content: Complete HTML document as string
        
    Returns:
        PDF content as bytes
        
    Raises:
        Exception: If PDF generation fails or dependencies missing
    """
    try:
        import weasyprint
        
        # Optimize HTML for PDF generation
        pdf_optimized_html = _optimize_html_for_pdf(html_content)
        
        # Generate PDF
        logger.info("Converting HTML to PDF")
        pdf_buffer = BytesIO()
        weasyprint.HTML(string=pdf_optimized_html).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        pdf_bytes = pdf_buffer.getvalue()
        logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes)")
        
        return pdf_bytes
        
    except ImportError:
        raise Exception("PDF generation requires 'weasyprint' package. Install with: pip install weasyprint")
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise Exception(f"PDF conversion failed: {str(e)}")

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
    
    Returns:
        Dict with dependency status and info
    """
    result = {
        'available': False,
        'missing_packages': [],
        'error_message': None
    }
    
    try:
        import weasyprint
        result['available'] = True
        result['weasyprint_version'] = weasyprint.__version__
        
    except ImportError as e:
        result['missing_packages'].append('weasyprint')
        result['error_message'] = str(e)
    
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