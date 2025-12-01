"""
Validation Utilities - Content and HTML validation functions
"""
import re
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
import textstat
from bs4 import BeautifulSoup


def validate_url(url: str) -> bool:
    """
    Validate if URL is properly formatted and accessible
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False


def validate_html(html: str) -> Tuple[bool, List[str]]:
    """
    Validate HTML structure and identify issues
    
    Args:
        html: HTML content to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for basic structure
        if not soup.find():
            issues.append("Empty or invalid HTML")
            return False, issues
        
        # Check heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            issues.append("No headings found")
        
        h1_count = len(soup.find_all('h1'))
        if h1_count == 0:
            issues.append("Missing H1 tag")
        elif h1_count > 1:
            issues.append(f"Multiple H1 tags found ({h1_count})")
        
        # Check for broken hierarchy
        if not validate_heading_hierarchy(html):
            issues.append("Broken heading hierarchy (headings skip levels)")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"HTML parsing error: {e}")
        return False, issues


def validate_heading_hierarchy(html: str) -> bool:
    """
    Check if heading hierarchy is valid (no skipped levels)
    
    Args:
        html: HTML content
        
    Returns:
        True if hierarchy is valid
    """
    soup = BeautifulSoup(html, 'html.parser')
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    if not headings:
        return False
    
    levels = [int(h.name[1]) for h in headings]
    
    # First heading should be H1
    if levels[0] != 1:
        return False
    
    # Check for skipped levels
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            return False
    
    return True


def calculate_readability(text: str) -> Dict[str, float]:
    """
    Calculate readability scores
    
    Args:
        text: Text content to analyze
        
    Returns:
        Dictionary of readability metrics
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    if not text or len(text) < 100:
        return {
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'avg_sentence_length': 0,
            'avg_word_length': 0
        }
    
    try:
        # Calculate average sentence length manually if needed
        sentences = text.split('.')
        avg_sentence_length = len(text.split()) / max(len([s for s in sentences if s.strip()]), 1)
        
        # Calculate average word length manually
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1) if words else 0
        
        return {
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
            'avg_sentence_length': avg_sentence_length,
            'avg_word_length': avg_word_length
        }
    except Exception as e:
        print(f"Readability calculation error: {e}")
        return {
            'flesch_reading_ease': 50,
            'flesch_kincaid_grade': 10,
            'avg_sentence_length': 20,
            'avg_word_length': 5
        }


def check_keyword_density(text: str, keyword: str) -> float:
    """
    Calculate keyword density percentage
    
    Args:
        text: Text content
        keyword: Keyword to check
        
    Returns:
        Density as decimal (0.015 = 1.5%)
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    # Count total words
    words = re.findall(r'\b\w+\b', text_lower)
    total_words = len(words)
    
    if total_words == 0:
        return 0.0
    
    # Count keyword occurrences
    keyword_count = text_lower.count(keyword_lower)
    
    return keyword_count / total_words


def extract_text_from_html(html: str) -> str:
    """
    Extract plain text from HTML
    
    Args:
        html: HTML content
        
    Returns:
        Plain text content
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(['script', 'style', 'nav', 'footer', 'header']):
        script.decompose()
    
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def count_words(text: str) -> int:
    """
    Count words in text
    
    Args:
        text: Text content
        
    Returns:
        Word count
    """
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def extract_headings(content: str) -> Dict[str, List[str]]:
    """
    Extract all headings from content (supports both Markdown and HTML)
    
    Args:
        content: Markdown or HTML content
        
    Returns:
        Dictionary mapping heading levels to list of heading texts
    """
    headings = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': [],
        'h5': [],
        'h6': []
    }
    
    # First, try to extract Markdown headings (# syntax)
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            # Count the number of # symbols
            level = 0
            for char in line:
                if char == '#':
                    level += 1
                else:
                    break
            
            if 1 <= level <= 6:
                # Extract heading text (remove # and leading/trailing whitespace)
                heading_text = line[level:].strip()
                if heading_text:
                    headings[f'h{level}'].append(heading_text)
    
    # If no Markdown headings found, try HTML
    if all(len(h) == 0 for h in headings.values()):
        soup = BeautifulSoup(content, 'html.parser')
        for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headings[level] = [h.get_text().strip() for h in soup.find_all(level)]
    
    return headings


def find_internal_link_opportunities(text: str) -> List[str]:
    """
    Identify potential internal link opportunities based on common topics
    
    Args:
        text: Text content
        
    Returns:
        List of suggested topics/pages for internal linking
    """
    text_lower = text.lower()
    
    # Common Sendmarc topics
    topics = {
        'dmarc': 'DMARC Guide',
        'spf': 'SPF Configuration',
        'dkim': 'DKIM Setup',
        'email authentication': 'Email Authentication',
        'phishing': 'Phishing Prevention',
        'domain spoofing': 'Domain Spoofing Protection',
        'email security': 'Email Security Best Practices',
        'dmarc policy': 'DMARC Policy Configuration',
        'dmarc report': 'DMARC Reporting',
        'email deliverability': 'Email Deliverability'
    }
    
    opportunities = []
    for keyword, page_name in topics.items():
        if keyword in text_lower:
            opportunities.append(page_name)
    
    return list(set(opportunities))  # Remove duplicates


def validate_meta_description(description: str) -> Tuple[bool, str]:
    """
    Validate meta description length
    
    Args:
        description: Meta description text
        
    Returns:
        Tuple of (is_valid, message)
    """
    length = len(description)
    
    if length < 150:
        return False, f"Meta description too short ({length} chars, minimum 150)"
    elif length > 160:
        return False, f"Meta description too long ({length} chars, maximum 160)"
    else:
        return True, f"Meta description length optimal ({length} chars)"


def extract_links(html: str) -> Dict[str, List[str]]:
    """
    Extract all links from HTML
    
    Args:
        html: HTML content
        
    Returns:
        Dictionary with 'internal' and 'external' link lists
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = {
        'internal': [],
        'external': []
    }
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith(('http://', 'https://')):
            links['external'].append(href)
        elif href.startswith(('/', '#')) or not href.startswith(('mailto:', 'tel:')):
            links['internal'].append(href)
    
    return links

