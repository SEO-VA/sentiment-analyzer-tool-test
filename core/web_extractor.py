import re
import time
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Optional, Tuple, Dict, Any

import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import streamlit as st

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class WebContentExtractor:
    """Extracts main content from web pages with JavaScript support"""
    
    def __init__(self, use_selenium: bool = True, timeout: int = 30):
        self.use_selenium = use_selenium
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }
        
        # Article detection regex
        self.article_hint_regex = re.compile(
            r"(article|content|post|entry|story|main|body|writeup|read|text|page)", re.I
        )
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract main content and structure from URL
        Returns: {
            'text': str,           # Raw text content for AI processing
            'structure': dict,     # HTML structure for reconstruction  
            'title': str,          # Page title
            'url': str,           # Original URL
            'success': bool,      # Extraction success
            'error': str          # Error message if failed
        }
        """
        try:
            logger.info(f"Starting content extraction for: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                return self._error_result("Invalid URL format", url)
            
            # Fetch HTML content
            html_content = self._fetch_html(url)
            if not html_content:
                return self._error_result("Failed to fetch page content", url)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")
            
            # Extract page title
            title = self._extract_title(soup)
            
            # Find main content node
            main_node = self._pick_main_node(soup)
            if not main_node:
                return self._error_result("Could not identify main content", url)
            
            # Parse structure and extract text
            structure_data = self._parse_structure(main_node)
            raw_text = self._extract_raw_text(main_node)
            
            # Validate content quality
            if len(raw_text.strip()) < 100:
                return self._error_result("Insufficient content extracted", url)
            
            logger.info(f"Successfully extracted {len(raw_text)} characters from {url}")
            
            return {
                'text': raw_text,
                'structure': structure_data,
                'title': title,
                'url': url,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            return self._error_result(f"Extraction error: {str(e)}", url)
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content, try requests first, fallback to Selenium if needed"""
        try:
            # Try static content first
            logger.info(f"Attempting static fetch for: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            
            # Quick content check
            soup = BeautifulSoup(html, "lxml")
            text_content = soup.get_text(" ", strip=True)
            
            if not self.use_selenium:
                return html
                
            # Check if we have substantial content or if Selenium is needed
            has_article = soup.find("article") is not None
            has_main = soup.find("main") is not None  
            sufficient_content = len(text_content) > 1000
            
            if has_article or has_main or sufficient_content:
                logger.info("Static content appears sufficient")
                return html
            
            # Fall back to Selenium for JS-heavy sites
            logger.info("Static content insufficient, using Selenium")
            return self._fetch_with_selenium(url)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Static fetch failed: {str(e)}, trying Selenium")
            if self.use_selenium:
                return self._fetch_with_selenium(url)
            return None
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """Fetch content using Selenium for JavaScript-heavy sites"""
        driver = None
        try:
            # Configure Chrome options for Streamlit Cloud
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--silent")
            chrome_options.add_argument(f"--user-agent={self.headers['User-Agent']}")
            
            # For Streamlit Cloud compatibility
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            
            # Initialize driver
            try:
                # Try to use system Chrome first (Streamlit Cloud)
                driver = webdriver.Chrome(options=chrome_options)
            except Exception:
                # Fallback to webdriver-manager (local development)
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            
            # Navigate to page
            logger.info(f"Loading page with Selenium: {url}")
            driver.get(url)
            
            # Handle cookie/consent popups
            self._handle_cookie_consent(driver)
            
            # Wait for content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            return driver.page_source
            
        except WebDriverException as e:
            logger.error(f"Selenium fetch failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Selenium fetch: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
    
    def _handle_cookie_consent(self, driver):
        """Handle common cookie consent popups"""
        consent_selectors = [
            # Common consent button patterns
            "//button[contains(translate(., 'ACCEPTALLOWOK', 'acceptallowok'), 'accept')]",
            "//button[contains(translate(., 'ACCEPTALLOWOK', 'acceptallowok'), 'allow')]", 
            "//button[contains(translate(., 'ACCEPTALLOWOK', 'acceptallowok'), 'ok')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Allow')]",
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Agree')]",
            "//a[contains(text(), 'Accept')]",
            # Finnish patterns
            "//button[contains(text(), 'Hyväksy')]",
            "//button[contains(text(), 'Salli')]",
        ]
        
        for selector in consent_selectors:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                logger.info(f"Clicked consent button: {selector}")
                time.sleep(1)
                break
            except TimeoutException:
                continue
            except Exception as e:
                logger.debug(f"Could not click consent button {selector}: {str(e)}")
                continue
    
    def _pick_main_node(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Pick the main content node using multiple strategies"""
        # Strategy 1: Direct article-like tags
        candidates = [
            soup.find("article"),
            soup.select_one('[role="article"]'),
            soup.select_one('main article'),
        ]
        
        for candidate in candidates:
            if candidate:
                logger.info(f"Found main content using article tag: {candidate.name}")
                return candidate
        
        # Strategy 2: Main/landmark elements
        main_candidates = [
            soup.select_one("main"),
            soup.select_one('[role="main"]'),
        ]
        
        for main in main_candidates:
            if main:
                # Look for best child within main
                best_child = self._best_child_by_density(main)
                if best_child:
                    logger.info(f"Found main content in main element child")
                    return best_child
                logger.info(f"Using main element directly")
                return main
        
        # Strategy 3: Schema.org markup
        schema = soup.select_one('[itemtype*="Article" i]')
        if schema:
            logger.info("Found main content using schema.org Article")
            return schema
        
        # Strategy 4: Heuristic class/id matching
        hints = soup.select("*[class], *[id]")
        good_candidates = []
        
        for el in hints:
            class_id = " ".join([
                el.get("id", ""), 
                " ".join(el.get("class", []))
            ]).strip()
            
            if class_id and self.article_hint_regex.search(class_id):
                good_candidates.append(el)
        
        if good_candidates:
            best = self._best_by_density(good_candidates)
            if best:
                logger.info("Found main content using heuristic class/id matching")
                return best
        
        # Strategy 5: Density scoring fallback
        body = soup.body or soup
        candidates = [c for c in body.find_all(recursive=False) if isinstance(c, Tag)]
        
        if not candidates:
            candidates = [c for c in body.descendants if isinstance(c, Tag)][:20]  # Limit search
        
        best = self._best_by_density(candidates)
        if best:
            logger.info("Found main content using density scoring")
            return best
        
        # Last resort: use body
        logger.warning("Using body as fallback for main content")
        return body
    
    def _node_score(self, el: Tag) -> float:
        """Score node by text density and content quality"""
        if not isinstance(el, Tag):
            return 0.0
            
        text = el.get_text(" ", strip=True)
        if not text:
            return 0.0
            
        text_len = len(text)
        
        # Calculate link density (too many links = navigation/sidebar)
        link_text_len = sum(len(a.get_text(" ", strip=True)) for a in el.find_all("a"))
        link_density = min(1.0, link_text_len / max(1, text_len))
        
        # Penalize navigation elements
        penalty = 0.6 if el.name in {"nav", "aside", "footer", "header"} else 1.0
        
        # Bonus for article-like elements
        bonus = 1.5 if el.name in {"article", "main", "section"} else 1.0
        
        return text_len * (1.0 - link_density) * penalty * bonus
    
    def _best_by_density(self, nodes: list) -> Optional[Tag]:
        """Find the node with highest content density"""
        scored = [(n, self._node_score(n)) for n in nodes if isinstance(n, Tag)]
        scored = [x for x in scored if x[1] > 0]
        
        if not scored:
            return None
            
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]
    
    def _best_child_by_density(self, parent: Tag) -> Optional[Tag]:
        """Find the best child element by density"""
        children = [c for c in parent.find_all(recursive=False) if isinstance(c, Tag)]
        return self._best_by_density(children)
    
    def _parse_structure(self, node: Tag) -> Dict[str, Any]:
        """Parse HTML structure for later reconstruction"""
        # Clone the node to avoid modifying original
        structure_soup = BeautifulSoup(str(node), "lxml")
        main_element = structure_soup.find() or structure_soup
        
        # Clean for structure preservation
        self._clean_for_structure(main_element)
        
        return {
            'html': str(main_element),
            'tag_name': main_element.name,
            'has_tables': len(main_element.find_all('table')) > 0,
            'has_lists': len(main_element.find_all(['ul', 'ol'])) > 0,
            'heading_count': len(main_element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'paragraph_count': len(main_element.find_all('p'))
        }
    
    def _clean_for_structure(self, node: Tag):
        """Clean HTML while preserving structure for reconstruction"""
        # Remove scripts, styles, and other non-content elements
        for bad in node.find_all(["script", "style", "noscript", "iframe", "embed", "object"]):
            bad.decompose()
        
        # Remove images but keep figure captions
        for fig in node.find_all("figure"):
            cap = fig.find("figcaption")
            if cap:
                fig.insert_before(cap.extract())
            fig.decompose()
        
        # Remove other media elements
        for media in node.find_all(["img", "picture", "source", "svg", "canvas", "video", "audio"]):
            media.decompose()
        
        # Keep links but prepare them for text extraction
        # (We'll handle link processing during text extraction)
    
    def _extract_raw_text(self, node: Tag) -> str:
        """Extract clean text content for AI processing"""
        # Clone for text extraction
        text_soup = BeautifulSoup(str(node), "lxml")
        text_element = text_soup.find() or text_soup
        
        # Clean for text extraction (more aggressive than structure cleaning)
        self._clean_for_text(text_element)
        
        # Convert <br> to newlines
        for br in text_element.find_all("br"):
            br.replace_with("\n")
        
        # Extract text
        text = text_element.get_text(separator="\n", strip=False)
        
        # Basic text normalization
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Collapse multiple newlines
        text = re.sub(r' +', ' ', text)  # Collapse multiple spaces
        text = text.strip()
        
        return text
    
    def _clean_for_text(self, node: Tag):
        """Clean HTML aggressively for text extraction"""
        # Remove all non-content elements
        for bad in node.find_all([
            "script", "style", "noscript", "iframe", "embed", "object",
            "figure", "img", "picture", "source", "svg", "canvas", "video", "audio"
        ]):
            bad.decompose()
        
        # Unwrap links (keep text, remove link)
        for link in node.find_all("a"):
            link.unwrap()
        
        # Remove navigation and sidebar elements
        for nav in node.find_all(["nav", "aside"]):
            nav.decompose()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
        
        return "Untitled Page"
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _error_result(self, error_message: str, url: str = "") -> Dict[str, Any]:
        """Create error result dictionary"""
        return {
            'text': "",
            'structure': {},
            'title': "",
            'url': url,
            'success': False,
            'error': error_message
        }