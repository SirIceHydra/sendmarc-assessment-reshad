"""
Stage 5: Original Content Generation - Outline
Generates detailed content outline using brand voice examples
"""
import os
import yaml
from typing import Dict, Any, List
from utils.llm_client import call_with_structured_output
from stages.stage4_rag_setup import retrieve_brand_examples


def load_prompts() -> Dict[str, Any]:
    """Load prompts from configuration"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'prompts.yaml'
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def format_brand_examples(examples: List[Dict[str, Any]]) -> str:
    """
    Format retrieved brand examples for prompt
    
    Args:
        examples: List of example chunks with metadata
        
    Returns:
        Formatted string
    """
    formatted = []
    
    for i, example in enumerate(examples, 1):
        metadata = example.get('metadata', {})
        content = example.get('content', '')
        
        formatted.append(f"""
Example {i} (Topic: {metadata.get('topic', 'N/A')}, Level: {metadata.get('technical_level', 'N/A')}):
{content[:500]}...
""")
    
    return '\n'.join(formatted)


def generate_outline(brief: Dict[str, Any], examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate detailed content outline
    
    Args:
        brief: Content brief from Stage 2
        examples: Retrieved brand voice examples
        
    Returns:
        Structured outline dictionary
    """
    print("Generating content outline...")
    
    prompts = load_prompts()['prompts']
    system_prompt = prompts['outline_generation']['system']
    context_prompt = prompts['outline_generation']['context'].format(
        brand_examples=format_brand_examples(examples)
    )
    
    # Format brief data
    topic = brief.get('target_topic', 'Email Security')
    primary_keyword = brief.get('primary_keyword', topic)
    secondary_keywords = ', '.join(brief.get('secondary_keywords', []))
    gaps = '\n'.join(f"- {gap}" for gap in brief.get('content_gaps', []))
    competitor_topics = '\n'.join(f"- {topic}" for topic in brief.get('competitor_structure', []))
    
    user_prompt = prompts['outline_generation']['user'].format(
        topic=topic,
        brief=str(brief),
        competitor_topics=competitor_topics,
        gaps=gaps,
        primary_keyword=primary_keyword,
        secondary_keywords=secondary_keywords
    )
    
    full_system = f"{system_prompt}\n\n{context_prompt}"
    
    try:
        outline = call_with_structured_output(
            prompt=user_prompt,
            system=full_system,
            temperature=0.7
        )
        
        print(f"✓ Outline generated with {len(outline.get('sections', []))} main sections")
        
        return outline
        
    except Exception as e:
        print(f"Outline generation failed: {e}")
        raise


def validate_outline(outline: Dict[str, Any], keywords: List[str]) -> tuple[bool, List[str]]:
    """
    Validate outline meets requirements
    
    Args:
        outline: Generated outline
        keywords: Target keywords
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check for required fields
    if not outline.get('h1'):
        issues.append("Missing H1 title")
    
    if not outline.get('meta_description'):
        issues.append("Missing meta description")
    
    if not outline.get('sections'):
        issues.append("Missing sections")
    
    # Check H1 contains primary keyword
    h1 = outline.get('h1', '').lower()
    if keywords and keywords[0].lower() not in h1:
        issues.append(f"Primary keyword '{keywords[0]}' not in H1")
    
    # Check section count
    sections = outline.get('sections', [])
    if len(sections) < 3:
        issues.append(f"Too few sections ({len(sections)}, minimum 3)")
    elif len(sections) > 7:
        issues.append(f"Too many sections ({len(sections)}, maximum 7)")
    
    # Check target word count
    target_wc = outline.get('target_word_count', 0)
    if target_wc < 1500 or target_wc > 2500:
        issues.append(f"Target word count out of range ({target_wc}, ideal 1500-2500)")
    
    return len(issues) == 0, issues


def run(pipeline_id: str, analysis_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Stage 5: Outline Generation
    
    Args:
        pipeline_id: Unique pipeline identifier
        analysis_output: Output from Stage 2
        
    Returns:
        Stage output dictionary
    """
    try:
        brief = analysis_output['content_brief']
        topic = brief.get('target_topic', 'Email Security')
        
        # Retrieve relevant brand examples
        print(f"Retrieving brand voice examples for topic: {topic}")
        examples = retrieve_brand_examples(topic, n=5)
        
        if not examples:
            print("Warning: No brand examples found, using generic Sendmarc voice")
            # Create a default example to help with generation
            examples = [{
                'content': 'Sendmarc provides authoritative, technically accurate content about email security and DMARC. We explain complex concepts clearly while maintaining professional expertise.',
                'metadata': {'topic': 'email_security', 'technical_level': 'intermediate'}
            }]
        
        # Generate outline
        outline = generate_outline(brief, examples)
        
        # Validate outline
        primary_keyword = brief.get('primary_keyword', '')
        is_valid, issues = validate_outline(outline, [primary_keyword])
        
        if not is_valid:
            print(f"⚠ Outline validation warnings: {', '.join(issues)}")
            # Don't fail, just warn
        
        return {
            'success': True,
            'outline': outline,
            'brand_examples_used': len(examples),
            'validation': {
                'is_valid': is_valid,
                'issues': issues
            }
        }
        
    except Exception as e:
        print(f"Stage 5 failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

