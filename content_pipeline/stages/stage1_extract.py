"""
Stage 1: Content Extraction
Extracts clean content from competitor URLs using Jina AI Reader and Trafilatura
"""
import os
import requests
import trafilatura
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def extract_with_jina(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract content using Jina AI Reader API
    
    Args:
        url: Target URL to extract
        
    Returns:
        Dictionary with extracted content or None on failure
    """
    try:
        jina_api_key = os.getenv('JINA_API_KEY')
        
        # Jina Reader API endpoint
        reader_url = f"https://r.jina.ai/{url}"
        
        headers = {}
        if jina_api_key:
            headers['Authorization'] = f'Bearer {jina_api_key}'
        
        response = requests.get(reader_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        
        # Parse metadata from markdown if available
        metadata = {
            'title': '',
            'description': '',
            'author': '',
            'publish_date': ''
        }
        
        # Extract title (first H1 or line)
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('# '):
                metadata['title'] = line.strip()[2:]
                break
        
        return {
            'content': content,
            'metadata': metadata,
            'extraction_method': 'jina',
            'success': True
        }
        
    except Exception as e:
        print(f"Jina extraction failed: {e}")
        return None


def extract_with_trafilatura(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract content using Trafilatura (fallback method)
    
    Args:
        url: Target URL to extract
        
    Returns:
        Dictionary with extracted content or None on failure
    """
    try:
        # Download the page with a browser-like User-Agent
        # Mimecast and others block default requests/trafilatura agents
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        downloaded = trafilatura.fetch_url(url)
        
        # If fetch_url fails or returns nothing, try requests with headers then pass to trafilatura
        if not downloaded:
            print("Trafilatura fetch failed, trying requests with headers...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            downloaded = response.text
        
        if not downloaded:
            return None
        
        # Extract content with better filtering
        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_formatting=True,
            output_format='markdown',
            include_links=True,
            favor_recall=False,  # Favor precision over recall (less navigation/menu content)
            favor_precision=True
        )
        
        if not content:
            return None
        
        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        
        metadata_dict = {
            'title': metadata.title if metadata and metadata.title else '',
            'description': metadata.description if metadata and metadata.description else '',
            'author': metadata.author if metadata and metadata.author else '',
            'publish_date': metadata.date if metadata and metadata.date else ''
        }
        
        return {
            'content': content,
            'metadata': metadata_dict,
            'extraction_method': 'trafilatura',
            'success': True
        }
        
    except Exception as e:
        print(f"Trafilatura extraction failed: {e}")
        return None


def validate_extraction(content: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate extracted content meets minimum requirements
    
    Args:
        content: Extraction result dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.get('success'):
        return False, "Extraction failed"
    
    text = content.get('content', '')
    
    if not text:
        return False, "No content extracted"
    
    # Count words
    word_count = len(text.split())
    
    if word_count < 500:
        return False, f"Content too short ({word_count} words, minimum 500)"
    
    return True, ""


def extract_content(url: str) -> Dict[str, Any]:
    """
    Main extraction function with fallback logic
    
    Args:
        url: Competitor blog URL
        
    Returns:
        Dictionary with extracted content and metadata
    """
    print(f"Stage 1: Extracting content from {url}")
    
    # Try Jina AI Reader first
    print("Attempting extraction with Jina AI Reader...")
    result = extract_with_jina(url)
    
    if result:
        is_valid, error = validate_extraction(result)
        if is_valid:
            print(f"✓ Jina extraction successful ({len(result['content'].split())} words)")
            result['source_url'] = url
            result['extracted_at'] = datetime.utcnow().isoformat()
            return result
        else:
            print(f"Jina extraction validation failed: {error}")
    
    # Fallback to Trafilatura
    print("Falling back to Trafilatura...")
    result = extract_with_trafilatura(url)
    
    if result:
        is_valid, error = validate_extraction(result)
        if is_valid:
            print(f"✓ Trafilatura extraction successful ({len(result['content'].split())} words)")
            result['source_url'] = url
            result['extracted_at'] = datetime.utcnow().isoformat()
            return result
        else:
            print(f"Trafilatura extraction validation failed: {error}")
            raise Exception(f"Content validation failed: {error}")
    
    raise Exception("All extraction methods failed")


def save_extraction(content: Dict[str, Any], extraction_id: str) -> None:
    """
    Save extracted content to filesystem
    
    Args:
        content: Extracted content dictionary
        extraction_id: Unique ID for this extraction
    """
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'extractions'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # Save markdown content
    content_file = os.path.join(output_dir, f"{extraction_id}.md")
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content['content'])
    
    print(f"Saved extraction to {content_file}")


# Main execution function
def run(pipeline_id: str, source_url: str) -> Dict[str, Any]:
    """
    Execute Stage 1: Content Extraction
    
    Args:
        pipeline_id: Unique pipeline identifier
        source_url: URL to extract content from
        
    Returns:
        Stage output dictionary
    """
    try:
        result = extract_content(source_url)
        save_extraction(result, pipeline_id)
        
        # Calculate word count for summary
        word_count = len(result['content'].split())
        
        return {
            'success': True,
            'source_url': source_url,
            'extraction_method': result['extraction_method'],
            'word_count': word_count,
            'metadata': result['metadata'],
            'extracted_at': result['extracted_at'],
            'content_preview': result['content'][:500] + '...' if len(result['content']) > 500 else result['content']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'source_url': source_url
        }

