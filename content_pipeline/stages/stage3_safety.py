"""
Stage 3: Safety & Ethics Gate
Performs plagiarism checks and copyright risk assessment
"""
import os
import yaml
import numpy as np
from typing import Dict, Any, List
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer


# Global model instance
_embedding_model = None


def get_embedding_model():
    """Get or create embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        print("Loading sentence transformer model...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def chunk_content(content: str, chunk_size: int = 500) -> List[str]:
    """
    Split content into chunks for embedding
    
    Args:
        content: Text content
        chunk_size: Target chunk size in words
        
    Returns:
        List of content chunks
    """
    words = content.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def generate_content_fingerprint(content: str) -> np.ndarray:
    """
    Generate embeddings for content chunks
    
    Args:
        content: Text content
        
    Returns:
        Numpy array of embeddings
    """
    print("Generating content fingerprint...")
    
    model = get_embedding_model()
    chunks = chunk_content(content)
    
    if not chunks:
        return np.array([])
    
    embeddings = model.encode(chunks)
    
    print(f"✓ Generated {len(embeddings)} chunk embeddings")
    
    return embeddings


def assess_copyright_risk(source_url: str, content: str) -> str:
    """
    Assess copyright risk based on source and content type
    
    Args:
        source_url: Source URL
        content: Content text
        
    Returns:
        Risk level: 'RED', 'YELLOW', or 'GREEN'
    """
    print("Assessing copyright risk...")
    
    # Load brand guidelines with risk sources
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'brand_guidelines.yaml'
    )
    
    with open(config_path, 'r') as f:
        guidelines = yaml.safe_load(f)
    
    domain = urlparse(source_url).netloc.lower()
    
    # Check against high-risk sources
    high_risk_domains = guidelines['competitor_sources']['high_risk']
    for high_risk in high_risk_domains:
        if high_risk in domain:
            print(f"⚠ HIGH RISK: Source is major publication ({domain})")
            return 'RED'
    
    # Check against medium-risk sources
    medium_risk_domains = guidelines['competitor_sources']['medium_risk']
    for medium_risk in medium_risk_domains:
        if medium_risk in domain:
            print(f"⚠ MEDIUM RISK: Source requires careful handling ({domain})")
            return 'YELLOW'
    
    # Check content characteristics for creative/narrative content
    word_count = len(content.split())
    
    # Very long-form content may be more creative
    if word_count > 3000:
        print(f"⚠ MEDIUM RISK: Long-form content ({word_count} words) may be highly creative")
        return 'YELLOW'
    
    print(f"✓ LOW RISK: Standard blog content from competitor source")
    return 'GREEN'


def check_sensitive_topics(content: str) -> List[str]:
    """
    Check if content covers sensitive topics requiring disclaimers
    
    Args:
        content: Content text
        
    Returns:
        List of sensitive topics found
    """
    content_lower = content.lower()
    
    sensitive_topics = {
        'legal_advice': ['legal advice', 'legal requirement', 'compliance requirement', 'must comply'],
        'financial_advice': ['investment', 'financial advice', 'roi guarantee'],
        'medical': ['medical', 'health advice', 'treatment'],
        'security_vulnerabilities': ['zero-day', 'exploit', 'vulnerability', 'cve-']
    }
    
    found_topics = []
    
    for topic, keywords in sensitive_topics.items():
        for keyword in keywords:
            if keyword in content_lower:
                found_topics.append(topic)
                break
    
    return list(set(found_topics))


def make_safety_decision(
    risk_level: str,
    sensitive_topics: List[str],
    source_url: str
) -> Dict[str, Any]:
    """
    Make final safety decision
    
    Args:
        risk_level: Copyright risk level
        sensitive_topics: List of sensitive topics
        source_url: Source URL
        
    Returns:
        Safety decision dictionary
    """
    print("Making safety decision...")
    
    decision = {
        'risk_level': risk_level,
        'sensitive_topics': sensitive_topics,
        'source_url': source_url,
        'proceed': True,
        'requires_human_review': False,
        'warnings': []
    }
    
    # RED: Halt pipeline
    if risk_level == 'RED':
        decision['proceed'] = False
        decision['requires_human_review'] = True
        decision['warnings'].append('Major publication with high creative content - PIPELINE HALTED')
        print("🛑 RED FLAG: Pipeline halted for review")
        return decision
    
    # YELLOW: Proceed with mandatory review
    if risk_level == 'YELLOW':
        decision['requires_human_review'] = True
        decision['warnings'].append('Medium risk source - mandatory human review required')
        print("⚠ YELLOW FLAG: Proceeding with mandatory review")
    
    # Check sensitive topics
    if sensitive_topics:
        decision['requires_human_review'] = True
        decision['warnings'].append(f'Sensitive topics detected: {", ".join(sensitive_topics)}')
        print(f"⚠ Sensitive topics: {', '.join(sensitive_topics)}")
    
    if decision['proceed']:
        print("✓ GREEN: Safe to proceed")
    
    return decision


def save_fingerprint(pipeline_id: str, fingerprint: np.ndarray) -> None:
    """
    Save content fingerprint for later plagiarism checking
    
    Args:
        pipeline_id: Unique pipeline identifier
        fingerprint: Embedding array
    """
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'fingerprints'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    fingerprint_file = os.path.join(output_dir, f"{pipeline_id}.npy")
    np.save(fingerprint_file, fingerprint)
    
    print(f"Saved content fingerprint to {fingerprint_file}")


def run(pipeline_id: str, extraction_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Stage 3: Safety & Ethics Gate
    
    Args:
        pipeline_id: Unique pipeline identifier
        extraction_output: Output from Stage 1
        
    Returns:
        Stage output dictionary
    """
    try:
        # Load the full content
        content_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'extractions',
            f"{pipeline_id}.md"
        )
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        source_url = extraction_output['source_url']
        
        # Generate content fingerprint
        fingerprint = generate_content_fingerprint(content)
        save_fingerprint(pipeline_id, fingerprint)
        
        # Assess copyright risk
        risk_level = assess_copyright_risk(source_url, content)
        
        # Check for sensitive topics
        sensitive_topics = check_sensitive_topics(content)
        
        # Make safety decision
        decision = make_safety_decision(risk_level, sensitive_topics, source_url)
        
        return {
            'success': True,
            'decision': decision,
            'fingerprint_chunks': len(fingerprint),
            'risk_assessment': {
                'copyright_risk': risk_level,
                'sensitive_topics': sensitive_topics,
                'requires_review': decision['requires_human_review'],
                'can_proceed': decision['proceed']
            }
        }
        
    except Exception as e:
        print(f"Stage 3 failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'decision': {
                'proceed': False,
                'risk_level': 'RED',
                'warnings': [f'Safety check failed: {str(e)}']
            }
        }

