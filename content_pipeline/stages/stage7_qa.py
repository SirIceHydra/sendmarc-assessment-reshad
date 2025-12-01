"""
Stage 7: Quality Assurance & Validation
Performs plagiarism checking, fact checking, SEO scoring, and brand voice validation
"""
import os
import yaml
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from utils.validation import (
    calculate_readability,
    check_keyword_density,
    count_words,
    validate_meta_description,
    find_internal_link_opportunities,
    extract_headings
)
from utils.llm_client import call_with_structured_output
from stages.stage4_rag_setup import get_embedding_model, chunk_content


def load_seo_rules() -> Dict[str, Any]:
    """Load SEO rules from configuration"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'seo_rules.yaml'
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def check_plagiarism(content: str, pipeline_id: str) -> Dict[str, Any]:
    """
    Check for plagiarism against competitor content
    
    Args:
        content: Generated content
        pipeline_id: Pipeline ID to load competitor fingerprint
        
    Returns:
        Plagiarism check results
    """
    print("Checking for plagiarism...")
    
    try:
        # Load competitor fingerprint
        fingerprint_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'fingerprints',
            f"{pipeline_id}.npy"
        )
        
        if not os.path.exists(fingerprint_file):
            print("Warning: No competitor fingerprint found")
            return {
                'max_similarity': 0.0,
                'flagged_chunks': [],
                'passed': True
            }
        
        competitor_embeddings = np.load(fingerprint_file)
        
        # Generate embeddings for new content
        model = get_embedding_model()
        new_chunks = chunk_content(content, chunk_size=500)
        new_embeddings = model.encode(new_chunks)
        
        # Calculate similarities
        similarities = cosine_similarity(new_embeddings, competitor_embeddings)
        max_similarities = similarities.max(axis=1)
        
        # Find flagged chunks (>0.85 similarity)
        threshold = 0.85
        flagged_indices = np.where(max_similarities > threshold)[0]
        
        flagged_chunks = []
        for idx in flagged_indices:
            flagged_chunks.append({
                'chunk_index': int(idx),
                'similarity': float(max_similarities[idx]),
                'content_preview': new_chunks[idx][:200] + '...'
            })
        
        max_sim = float(max_similarities.max()) if len(max_similarities) > 0 else 0.0
        
        result = {
            'max_similarity': max_sim,
            'avg_similarity': float(max_similarities.mean()) if len(max_similarities) > 0 else 0.0,
            'flagged_chunks': flagged_chunks,
            'passed': max_sim < threshold,
            'threshold': threshold
        }
        
        if not result['passed']:
            print(f"⚠ PLAGIARISM WARNING: Max similarity {max_sim:.2%} exceeds threshold")
        else:
            print(f"✓ Plagiarism check passed (max similarity: {max_sim:.2%})")
        
        return result
        
    except Exception as e:
        print(f"Plagiarism check error: {e}")
        return {
            'max_similarity': 0.0,
            'flagged_chunks': [],
            'passed': True,
            'error': str(e)
        }


def fact_check(content: str) -> List[Dict[str, Any]]:
    """
    Identify claims that need fact checking
    
    Args:
        content: Content to check
        
    Returns:
        List of claims to verify
    """
    print("Performing fact check analysis...")
    
    try:
        prompts_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config',
            'prompts.yaml'
        )
        
        with open(prompts_path, 'r') as f:
            prompts = yaml.safe_load(f)['prompts']
        
        system_prompt = prompts['fact_checking']['system']
        user_prompt = prompts['fact_checking']['user'].format(content=content)
        
        result = call_with_structured_output(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3
        )
        
        claims = result.get('claims', [])
        print(f"✓ Identified {len(claims)} factual claims")
        
        return claims
        
    except Exception as e:
        print(f"Fact checking error: {e}")
        return []


def score_seo(content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive SEO score
    
    Args:
        content: Content to score
        metadata: Article metadata
        
    Returns:
        SEO scoring results
    """
    print("Calculating SEO score...")
    
    rules = load_seo_rules()
    thresholds = rules['thresholds']
    scoring = rules['scoring']
    
    # Extract text without markdown
    text = content.replace('#', '').replace('*', '').replace('_', '')
    
    # Word count
    word_count = count_words(text)
    word_count_score = 0
    if word_count >= thresholds['word_count']['min']:
        word_count_score += 50
    if thresholds['word_count']['min'] <= word_count <= thresholds['word_count']['max']:
        word_count_score += 50
    
    # Readability
    readability = calculate_readability(text)
    flesch_score = readability['flesch_reading_ease']
    
    readability_score = 0
    if thresholds['readability']['flesch_reading_ease']['ideal_min'] <= flesch_score <= thresholds['readability']['flesch_reading_ease']['ideal_max']:
        readability_score = 100
    elif thresholds['readability']['flesch_reading_ease']['min'] <= flesch_score <= thresholds['readability']['flesch_reading_ease']['max']:
        readability_score = 60
    
    # Keyword optimization
    primary_keyword = metadata.get('target_keywords', {}).get('primary', metadata.get('title', '').split()[0])
    
    keyword_score = 0
    h1 = metadata.get('h1', '')
    if primary_keyword.lower() in h1.lower():
        keyword_score += scoring['keyword_optimization']['primary_in_h1']
    
    # Check first paragraph
    first_para = text.split('\n')[0] if text else ''
    if primary_keyword.lower() in first_para.lower():
        keyword_score += scoring['keyword_optimization']['primary_in_intro']
    
    # Keyword density
    density = check_keyword_density(text, primary_keyword)
    if thresholds['keyword_density']['primary']['min'] <= density <= thresholds['keyword_density']['primary']['max']:
        keyword_score += scoring['keyword_optimization']['primary_density_ideal']
    
    # Structure scoring
    headings = extract_headings(content)
    structure_score = 0
    
    if len(headings['h1']) == 1:
        structure_score += scoring['structure']['h1_present']
    
    h2_count = len(headings['h2'])
    if thresholds['heading_structure']['min_h2_sections'] <= h2_count <= thresholds['heading_structure']['max_h2_sections']:
        structure_score += scoring['structure']['h2_count_ideal']
    
    # Check heading hierarchy
    if len(headings['h1']) > 0 and len(headings['h2']) > 0:
        structure_score += scoring['structure']['heading_hierarchy']
    
    # Internal linking
    internal_links = find_internal_link_opportunities(text)
    internal_link_score = 0
    if len(internal_links) >= thresholds['internal_links']['min']:
        internal_link_score += 50
    if len(internal_links) >= thresholds['internal_links']['ideal']:
        internal_link_score += 50
    
    # Meta optimization
    meta_score = 0
    meta_desc = metadata.get('meta_description', '')
    is_valid, msg = validate_meta_description(meta_desc)
    if is_valid:
        meta_score += scoring['meta_optimization']['description_length']
    if primary_keyword.lower() in meta_desc.lower():
        meta_score += scoring['meta_optimization']['description_includes_keyword']
    
    # Calculate weighted total
    weights = scoring['weights']
    total_score = (
        (keyword_score / 100) * weights['keyword_optimization'] * 100 +
        (readability_score / 100) * weights['readability'] * 100 +
        (structure_score / 100) * weights['structure'] * 100 +
        (word_count_score / 100) * weights['content_length'] * 100 +
        (internal_link_score / 100) * weights['internal_linking'] * 100 +
        (meta_score / 100) * weights['meta_optimization'] * 100
    )
    
    result = {
        'total_score': round(total_score, 1),
        'component_scores': {
            'keyword_optimization': round(keyword_score, 1),
            'readability': round(readability_score, 1),
            'structure': round(structure_score, 1),
            'content_length': round(word_count_score, 1),
            'internal_linking': round(internal_link_score, 1),
            'meta_optimization': round(meta_score, 1)
        },
        'metrics': {
            'word_count': word_count,
            'flesch_reading_ease': round(flesch_score, 1),
            'keyword_density': round(density * 100, 2),
            'h2_count': h2_count,
            'internal_link_opportunities': len(internal_links)
        }
    }
    
    print(f"✓ SEO Score: {result['total_score']}/100")
    
    return result


def generate_quality_report(
    plagiarism_results: Dict[str, Any],
    fact_check_results: List[Dict[str, Any]],
    seo_results: Dict[str, Any],
    content: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive quality report
    
    Args:
        plagiarism_results: Plagiarism check results
        fact_check_results: Fact check results
        seo_results: SEO scoring results
        content: Article content
        metadata: Article metadata
        
    Returns:
        Quality report with flags and recommendations
    """
    print("Generating quality report...")
    
    rules = load_seo_rules()
    blocking_rules = rules['validation_rules']['blocking']
    warning_rules = rules['validation_rules']['warning']
    
    blocking_issues = []
    warnings = []
    
    # Plagiarism blocking
    if not plagiarism_results['passed']:
        blocking_issues.append(f"High plagiarism similarity detected: {plagiarism_results['max_similarity']:.2%}")
    
    # SEO blocking issues
    if 'h1' not in metadata or not metadata['h1']:
        blocking_issues.append("Missing H1 tag")
    
    if not metadata.get('meta_description'):
        blocking_issues.append("Missing meta description")
    
    # Use thresholds from config for readability blocking
    # Note: Technical content about DMARC/SPF/DKIM inherently has lower Flesch scores
    # due to multi-syllable technical terminology (authentication, configuration, etc.)
    flesch = seo_results['metrics']['flesch_reading_ease']
    flesch_min = rules['thresholds']['readability']['flesch_reading_ease']['min']
    flesch_max = rules['thresholds']['readability']['flesch_reading_ease']['max']
    if flesch < flesch_min:
        blocking_issues.append(f"Readability too low (Flesch: {flesch})")
    elif flesch > flesch_max:
        blocking_issues.append(f"Readability too high (Flesch: {flesch})")
    
    # Warnings
    word_count = seo_results['metrics']['word_count']
    if word_count < 1500:
        warnings.append(f"Word count below ideal ({word_count} words)")
    elif word_count > 3000:
        warnings.append(f"Word count above maximum ({word_count} words)")
    
    density = seo_results['metrics']['keyword_density']
    if density < 0.5:
        warnings.append(f"Keyword density low ({density}%)")
    elif density > 2.5:
        warnings.append(f"Keyword density high ({density}%)")
    
    if seo_results['metrics']['internal_link_opportunities'] < 2:
        warnings.append("Insufficient internal linking opportunities")
    
    # Fact check warnings
    high_confidence_claims = [c for c in fact_check_results if c.get('verification_needed', False)]
    if high_confidence_claims:
        warnings.append(f"{len(high_confidence_claims)} claims require verification")
    
    report = {
        'overall_status': 'PASS' if len(blocking_issues) == 0 else 'BLOCKED',
        'blocking_issues': blocking_issues,
        'warnings': warnings,
        'scores': {
            'seo_score': seo_results['total_score'],
            'plagiarism_max_similarity': plagiarism_results['max_similarity'],
            'readability_score': flesch
        },
        'metrics': seo_results['metrics'],
        'recommendations': []
    }
    
    # Generate recommendations
    if word_count < 1500:
        report['recommendations'].append("Expand content to meet minimum word count")
    
    if seo_results['total_score'] < 70:
        report['recommendations'].append("Improve SEO optimization (target: 70+)")
    
    if density < 0.5:
        report['recommendations'].append("Increase primary keyword usage naturally")
    
    if len(blocking_issues) > 0:
        print(f"🛑 QUALITY CHECK BLOCKED: {len(blocking_issues)} blocking issues")
    elif len(warnings) > 0:
        print(f"⚠ Quality warnings: {len(warnings)} issues")
    else:
        print("✓ Quality check passed")
    
    return report


def run(
    pipeline_id: str,
    draft_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Stage 7: Quality Assurance & Validation
    
    Args:
        pipeline_id: Unique pipeline identifier
        draft_output: Output from Stage 6
        
    Returns:
        Stage output dictionary
    """
    try:
        content = draft_output['content']
        metadata = draft_output['metadata']
        
        # Run all checks
        plagiarism_results = check_plagiarism(content, pipeline_id)
        fact_check_results = fact_check(content)
        seo_results = score_seo(content, metadata)
        
        # Generate quality report
        quality_report = generate_quality_report(
            plagiarism_results,
            fact_check_results,
            seo_results,
            content,
            metadata
        )
        
        return {
            'success': True,
            'quality_report': quality_report,
            'plagiarism_check': plagiarism_results,
            'fact_check': fact_check_results,
            'seo_analysis': seo_results
        }
        
    except Exception as e:
        print(f"Stage 7 failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

