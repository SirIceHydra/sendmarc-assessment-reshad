"""
Stage 6: Original Content Generation - Full Draft
Generates complete article following the outline
"""
import os
import yaml
from typing import Dict, Any
from utils.llm_client import call_gemini


def load_prompts() -> Dict[str, Any]:
    """Load prompts from configuration"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'prompts.yaml'
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def format_outline_for_prompt(outline: Dict[str, Any]) -> str:
    """
    Format outline into readable structure for prompt
    
    Args:
        outline: Outline dictionary
        
    Returns:
        Formatted outline string
    """
    formatted = [f"# {outline.get('h1', 'Article Title')}"]
    formatted.append(f"\nMeta Description: {outline.get('meta_description', '')}")
    formatted.append(f"Target Word Count: {outline.get('target_word_count', 2000)}\n")
    
    sections = outline.get('sections', [])
    for section in sections:
        formatted.append(f"\n## {section.get('h2', 'Section Title')}")
        
        key_points = section.get('key_points', [])
        if key_points:
            formatted.append("Key Points:")
            for point in key_points:
                formatted.append(f"  - {point}")
        
        subsections = section.get('subsections', [])
        if subsections:
            for subsection in subsections:
                formatted.append(f"\n### {subsection.get('h3', 'Subsection')}")
                notes = subsection.get('content_notes', '')
                if notes:
                    formatted.append(f"Notes: {notes}")
    
    return '\n'.join(formatted)


def format_brand_examples(examples: list) -> str:
    """Format brand examples for context"""
    if not examples:
        return "Use professional, authoritative tone with technical accuracy."
    
    formatted = []
    for i, example in enumerate(examples[:3], 1):  # Limit to 3 to save tokens
        content = example.get('content', '')[:400]  # Truncate for token limit
        formatted.append(f"Example {i}:\n{content}...\n")
    
    return '\n'.join(formatted)


def generate_full_draft(
    outline: Dict[str, Any],
    brief: Dict[str, Any],
    brand_examples: list
) -> str:
    """
    Generate full article content
    
    Args:
        outline: Structured outline
        brief: Content brief
        brand_examples: Retrieved brand voice examples
        
    Returns:
        Generated markdown content
    """
    print("Generating full article draft...")
    
    prompts = load_prompts()['prompts']
    system_prompt = prompts['full_draft_generation']['system']
    context_prompt = prompts['full_draft_generation']['context'].format(
        brand_examples=format_brand_examples(brand_examples)
    )
    
    # Format data for prompt
    outline_text = format_outline_for_prompt(outline)
    brief_text = f"""
Target Topic: {brief.get('target_topic')}
Target Audience: {brief.get('target_audience')}
Technical Level: {brief.get('technical_level')}
Content Gaps to Fill: {', '.join(brief.get('content_gaps', []))}
Unique Angles: {', '.join(brief.get('unique_angles', []))}
"""
    
    primary_keyword = brief.get('primary_keyword', '')
    secondary_keywords = ', '.join(brief.get('secondary_keywords', []))
    keywords_text = f"Primary: {primary_keyword}\nSecondary: {secondary_keywords}"
    
    user_prompt = prompts['full_draft_generation']['user'].format(
        outline=outline_text,
        brief=brief_text,
        keywords=keywords_text
    )
    
    full_system = f"{system_prompt}\n\n{context_prompt}"
    
    try:
        # Use higher temperature for more creative writing
        content = call_gemini(
            prompt=user_prompt,
            system=full_system,
            temperature=0.8
        )
        
        # Check if content appears truncated (ends mid-sentence or very abruptly)
        word_count = len(content.split())
        if content.strip() and not content.rstrip().endswith(('.', '!', '?', ':', ';')):
            # Content might be truncated - check last 100 chars
            last_chars = content.rstrip()[-100:]
            if not any(last_chars.endswith(ending) for ending in ['.', '!', '?', ':', ';', ')', ']', '}']):
                print(f"⚠ Warning: Content may be truncated (ends with: ...{last_chars[-30:]})")
        
        print(f"✓ Generated article draft ({word_count} words)")
        
        # Ensure content starts properly (remove any markdown code block markers if present)
        if content.strip().startswith('```'):
            lines = content.split('\n')
            # Remove first line if it's ```markdown or ```
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        return content
        
    except Exception as e:
        print(f"Draft generation failed: {e}")
        raise


def validate_draft(content: str, outline: Dict[str, Any]) -> tuple[bool, list]:
    """
    Validate generated draft
    
    Args:
        content: Generated markdown content
        outline: Original outline
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Validate outline first
    if not outline or not isinstance(outline, dict):
        issues.append(f"Invalid outline provided: {type(outline)}")
        return False, issues
    
    # Word count check
    word_count = len(content.split())
    if word_count < 1200:
        issues.append(f"Content too short ({word_count} words, minimum 1200)")
    elif word_count > 3500:
        issues.append(f"Content too long ({word_count} words, maximum 3500)")
    
    # Check for H1
    if not content.strip().startswith('#'):
        issues.append("Content doesn't start with H1")
    
    # Check for multiple H2 sections
    h2_count = content.count('\n## ')
    if h2_count < 3:
        issues.append(f"Too few H2 sections ({h2_count}, minimum 3)")
    
    # Check for primary keyword in first paragraph
    lines = content.split('\n')
    first_para = ''
    for line in lines[1:]:  # Skip H1
        if line.strip() and not line.startswith('#'):
            first_para = line
            break
    
    primary_keyword = outline.get('h1', '').split()[0] if outline.get('h1') else ''  # Rough check
    if primary_keyword and primary_keyword.lower() not in first_para.lower():
        issues.append("Primary keyword not in first paragraph")
    
    return len(issues) == 0, issues


def extract_metadata_from_draft(content: str, outline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from generated draft
    
    Args:
        content: Generated content
        outline: Original outline
        
    Returns:
        Metadata dictionary
    """
    if not outline or not isinstance(outline, dict):
        raise ValueError(f"Invalid outline provided: {type(outline)}")
    
    # Extract title (first H1)
    lines = content.split('\n')
    title = outline.get('h1', '')
    
    for line in lines:
        if line.strip().startswith('# '):
            title = line.strip()[2:]
            break
    
    return {
        'title': title,
        'meta_description': outline.get('meta_description', ''),
        'slug': outline.get('slug', ''),
        'word_count': len(content.split()),
        'h1': title,
        'target_keywords': {
            'primary': outline.get('h1', '').split()[0],  # Simplified
            'secondary': []
        }
    }


def run(
    pipeline_id: str,
    outline_output: Dict[str, Any],
    analysis_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Stage 6: Full Draft Generation
    
    Args:
        pipeline_id: Unique pipeline identifier
        outline_output: Output from Stage 5
        analysis_output: Output from Stage 2
        
    Returns:
        Stage output dictionary
    """
    try:
        # DEBUG: Log what we receive
        print(f"\n[DEBUG Stage 6] Received outline_output type: {type(outline_output)}")
        print(f"[DEBUG Stage 6] outline_output keys: {list(outline_output.keys()) if isinstance(outline_output, dict) else 'NOT A DICT'}")
        
        # Validate inputs first
        if not isinstance(outline_output, dict):
            raise TypeError(f"outline_output must be a dict, got {type(outline_output)}")
        
        if not isinstance(analysis_output, dict):
            raise TypeError(f"analysis_output must be a dict, got {type(analysis_output)}")
        
        # Check if stage 5 succeeded
        if not outline_output.get('success', False):
            error_msg = outline_output.get('error', 'Unknown error')
            raise Exception(f"Stage 5 failed: {error_msg}")
        
        # Check if outline exists - use .get() to avoid KeyError
        if 'outline' not in outline_output:
            available_keys = list(outline_output.keys())
            print(f"[DEBUG Stage 6] ERROR: 'outline' key missing! Available keys: {available_keys}")
            raise KeyError(f"Stage 5 output missing 'outline' key. Available keys: {available_keys}. Stage 5 may have failed.")
        
        print(f"[DEBUG Stage 6] 'outline' key exists in outline_output")
        
        # Use .get() to avoid KeyError, then validate
        outline = outline_output.get('outline')
        print(f"[DEBUG Stage 6] Got outline, type: {type(outline)}")
        
        if outline is None:
            raise ValueError("Outline is None in Stage 5 output. Stage 5 may have failed to generate outline.")
        
        # Validate outline
        if not isinstance(outline, dict):
            raise Exception(f"Outline must be a dictionary, got {type(outline)}")
        
        if not outline:
            raise Exception("Outline is empty. Stage 5 may have failed to generate outline.")
        
        print(f"[DEBUG Stage 6] Outline keys: {list(outline.keys())}")
        
        # Validate outline has required keys
        required_keys = ['h1', 'sections']
        missing_keys = [key for key in required_keys if key not in outline]
        if missing_keys:
            raise KeyError(f"Outline missing required keys: {missing_keys}. Available keys: {list(outline.keys())}")
        
        print(f"[DEBUG Stage 6] Outline validation passed, proceeding to generate draft...")
        
        # Check if analysis output is valid
        if not analysis_output.get('success', False):
            raise Exception(f"Stage 2 failed: {analysis_output.get('error', 'Unknown error')}")
        
        if 'content_brief' not in analysis_output:
            raise Exception("Stage 2 output missing 'content_brief' key.")
        
        brief = analysis_output['content_brief']
        
        # Get brand examples (retrieve again or use cached)
        from stages.stage4_rag_setup import retrieve_brand_examples
        topic = brief.get('target_topic', '')
        brand_examples = retrieve_brand_examples(topic, n=3)
        
        if not brand_examples:
            # Create default example
            brand_examples = [{
                'content': 'Sendmarc provides authoritative, technically accurate content about email security and DMARC. We explain complex concepts clearly while maintaining professional expertise.',
                'metadata': {'topic': 'email_security', 'technical_level': 'intermediate'}
            }]
        
        # Generate full draft
        content = generate_full_draft(outline, brief, brand_examples)
        
        # Validate draft
        is_valid, issues = validate_draft(content, outline)
        
        if not is_valid:
            print(f"⚠ Draft validation warnings: {', '.join(issues)}")
        
        # Extract metadata
        metadata = extract_metadata_from_draft(content, outline)
        
        # Save draft to file
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'drafts'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        draft_file = os.path.join(output_dir, f"{pipeline_id}.md")
        with open(draft_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved draft to {draft_file}")
        
        return {
            'success': True,
            'content': content,
            'metadata': metadata,
            'validation': {
                'is_valid': is_valid,
                'issues': issues
            },
            'draft_file': draft_file
        }
        
    except KeyError as e:
        error_msg = f"Missing key in data: {e}. This usually means a previous stage failed or returned incomplete data."
        print(f"Stage 6 failed: {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        # If it's just a key name, provide more context
        if error_msg in ["'outline'", "'content_brief'", "'brief'"]:
            error_msg = f"Missing required data key {error_msg}. A previous stage may have failed. Check Stage 5 output for outline issues."
        print(f"Stage 6 failed: {error_msg}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': error_msg
        }

