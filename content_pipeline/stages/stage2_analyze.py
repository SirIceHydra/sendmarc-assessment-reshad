"""
Stage 2: Content Intelligence Analysis
Analyzes competitor content and conducts keyword research
"""
import os
import yaml
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from utils.llm_client import call_with_structured_output, call_gemini

load_dotenv()


def load_prompts() -> Dict[str, Any]:
    """Load prompts from configuration"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config',
        'prompts.yaml'
    )
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def analyze_content(content: str) -> Dict[str, Any]:
    """
    Analyze competitor content using Gemini
    
    Args:
        content: Cleaned markdown content
        
    Returns:
        Analysis results dictionary
    """
    print("Analyzing content with Gemini...")
    
    prompts = load_prompts()['prompts']
    system_prompt = prompts['content_analysis']['system']
    user_prompt = prompts['content_analysis']['user'].format(content=content)
    
    try:
        analysis = call_with_structured_output(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7
        )
        
        print(f"✓ Content analysis complete")
        print(f"  Main topic: {analysis.get('main_topic', 'N/A')}")
        print(f"  Subtopics: {len(analysis.get('subtopics', []))}")
        
        return analysis
        
    except Exception as e:
        print(f"Content analysis failed: {e}")
        return {
            'main_topic': 'Unknown',
            'subtopics': [],
            'key_arguments': [],
            'target_audience': 'Unknown',
            'technical_level': 'intermediate',
            'content_structure': [],
            'missing_elements': []
        }


def extract_semantic_keywords(content: str) -> Dict[str, List[str]]:
    """
    Extract keywords using LLM
    
    Args:
        content: Content to analyze
        
    Returns:
        Dictionary of keyword categories
    """
    print("Extracting semantic keywords...")
    
    prompts = load_prompts()['prompts']
    system_prompt = prompts['keyword_extraction']['system']
    user_prompt = prompts['keyword_extraction']['user'].format(content=content)
    
    try:
        keywords = call_with_structured_output(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.5
        )
        
        print(f"✓ Extracted {len(keywords.get('primary_keywords', []))} primary keywords")
        
        return keywords
        
    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return {
            'primary_keywords': [],
            'secondary_keywords': [],
            'long_tail_phrases': [],
            'related_topics': []
        }


def research_keywords(topic: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Research keywords using SerpAPI
    
    Args:
        topic: Main topic
        keywords: List of keywords to research
        
    Returns:
        List of keyword research results
    """
    print(f"Researching keywords via SerpAPI...")
    
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    if not serpapi_key:
        print("Warning: SERPAPI_KEY not found, skipping keyword research")
        return []
    
    results = []
    
    # Limit to top 5 keywords to stay within free tier
    for keyword in keywords[:5]:
        try:
            params = {
                'q': keyword,
                'api_key': serpapi_key,
                'engine': 'google'
            }
            
            response = requests.get('https://serpapi.com/search', params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant SERP features
            result = {
                'keyword': keyword,
                'search_results_count': data.get('search_information', {}).get('total_results', 0),
                'has_featured_snippet': 'answer_box' in data,
                'has_people_also_ask': 'related_questions' in data,
                'related_searches': [r.get('query', '') for r in data.get('related_searches', [])[:3]]
            }
            
            results.append(result)
            print(f"  ✓ {keyword}: {result['search_results_count']} results")
            
        except Exception as e:
            print(f"  ✗ Keyword research failed for '{keyword}': {e}")
            results.append({
                'keyword': keyword,
                'error': str(e)
            })
    
    return results


def perform_gap_analysis(competitor_data: Dict[str, Any], topic: str) -> Dict[str, Any]:
    """
    Identify content gaps and opportunities
    
    Args:
        competitor_data: Analyzed competitor content
        topic: Main topic
        
    Returns:
        Gap analysis results
    """
    print("Performing gap analysis...")
    
    # Use LLM to identify gaps
    prompt = f"""
    Analyze this competitor content summary and identify opportunities for Sendmarc to add unique value.
    
    Competitor Coverage:
    - Main Topic: {competitor_data.get('main_topic')}
    - Subtopics: {', '.join(competitor_data.get('subtopics', []))}
    - Key Arguments: {', '.join(competitor_data.get('key_arguments', []))}
    - Missing Elements: {', '.join(competitor_data.get('missing_elements', []))}
    
    Sendmarc's Unique Strengths:
    - DMARC implementation expertise
    - Email authentication technical depth
    - Real-world threat intelligence
    - Practical security use cases
    
    Identify 3-5 specific gaps or angles Sendmarc can fill that the competitor missed.
    Output as JSON:
    {{
        "gaps": ["gap 1", "gap 2", ...],
        "unique_angles": ["angle 1", "angle 2", ...],
        "value_propositions": ["proposition 1", "proposition 2", ...]
    }}
    """
    
    try:
        gaps = call_with_structured_output(prompt, temperature=0.7)
        print(f"✓ Identified {len(gaps.get('gaps', []))} content gaps")
        return gaps
    except Exception as e:
        print(f"Gap analysis failed: {e}")
        return {
            'gaps': [],
            'unique_angles': [],
            'value_propositions': []
        }


def generate_content_brief(
    analysis: Dict[str, Any],
    keywords_data: Dict[str, Any],
    gaps: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive content brief
    
    Args:
        analysis: Content analysis results
        keywords_data: Keyword research results
        gaps: Gap analysis results
        
    Returns:
        Content brief dictionary
    """
    print("Generating content brief...")
    
    # Combine extracted and researched keywords
    all_keywords = keywords_data.get('primary_keywords', [])
    
    brief = {
        'target_topic': analysis.get('main_topic'),
        'target_audience': analysis.get('target_audience'),
        'technical_level': analysis.get('technical_level'),
        'primary_keyword': all_keywords[0] if all_keywords else analysis.get('main_topic'),
        'secondary_keywords': all_keywords[1:4] if len(all_keywords) > 1 else [],
        'content_gaps': gaps.get('gaps', []),
        'unique_angles': gaps.get('unique_angles', []),
        'value_propositions': gaps.get('value_propositions', []),
        'competitor_structure': analysis.get('content_structure', []),
        'suggested_improvements': analysis.get('missing_elements', [])
    }
    
    print("✓ Content brief generated")
    return brief


def run(pipeline_id: str, extraction_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Stage 2: Content Intelligence Analysis
    
    Args:
        pipeline_id: Unique pipeline identifier
        extraction_output: Output from Stage 1
        
    Returns:
        Stage output dictionary
    """
    try:
        # Load the full content from extraction
        content_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'extractions',
            f"{pipeline_id}.md"
        )
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analyze content
        analysis = analyze_content(content)
        
        # Extract keywords
        keywords_data = extract_semantic_keywords(content)
        
        # Research keywords (limited for free tier)
        keyword_research = research_keywords(
            analysis.get('main_topic', ''),
            keywords_data.get('primary_keywords', [])
        )
        
        # Perform gap analysis
        gaps = perform_gap_analysis(analysis, analysis.get('main_topic', ''))
        
        # Generate content brief
        brief = generate_content_brief(analysis, keywords_data, gaps)
        
        return {
            'success': True,
            'analysis': analysis,
            'keywords': keywords_data,
            'keyword_research': keyword_research,
            'gap_analysis': gaps,
            'content_brief': brief
        }
        
    except Exception as e:
        print(f"Stage 2 failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

