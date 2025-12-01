"""
Stage 8: HTML Structuring & Production Formatting
Converts markdown to production-ready HTML with proper structure and metadata
"""
import os
import json
from typing import Dict, Any
import markdown
from jinja2 import Template
from datetime import datetime
from utils.validation import validate_html


def markdown_to_html(content: str) -> str:
    """
    Convert markdown to HTML with extensions
    
    Args:
        content: Markdown content
        
    Returns:
        HTML content
    """
    print("Converting markdown to HTML...")
    
    md = markdown.Markdown(extensions=[
        'extra',  # Tables, fenced code blocks, etc.
        'toc',    # Table of contents
        'nl2br',  # Newline to break
        'sane_lists'
    ])
    
    html = md.convert(content)
    
    return html


def generate_schema_markup(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Schema.org Article markup
    
    Args:
        metadata: Article metadata
        
    Returns:
        Schema.org JSON-LD dictionary
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": metadata.get('title', ''),
        "description": metadata.get('meta_description', ''),
        "author": {
            "@type": "Organization",
            "name": "Sendmarc"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Sendmarc",
            "logo": {
                "@type": "ImageObject",
                "url": "https://sendmarc.com/logo.png"
            }
        },
        "datePublished": datetime.utcnow().isoformat(),
        "dateModified": datetime.utcnow().isoformat()
    }
    
    return schema


def apply_template(html: str, metadata: Dict[str, Any], schema: Dict[str, Any]) -> str:
    """
    Apply Jinja2 template with Sendmarc styling
    
    Args:
        html: HTML content
        metadata: Article metadata
        schema: Schema.org markup
        
    Returns:
        Complete HTML with template
    """
    print("Applying HTML template...")
    
    template_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    
    <!-- Meta Tags -->
    <meta name="description" content="{{ meta_description }}">
    <meta name="author" content="Sendmarc">
    
    <!-- OpenGraph Tags -->
    <meta property="og:title" content="{{ title }}">
    <meta property="og:description" content="{{ meta_description }}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Sendmarc">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ title }}">
    <meta name="twitter:description" content="{{ meta_description }}">
    
    <!-- Schema.org Markup -->
    <script type="application/ld+json">
    {{ schema_json }}
    </script>
    
    <!-- Sendmarc Styles (placeholder - replace with actual stylesheet) -->
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        article {
            background: #fff;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 0.5em;
            color: #1a1a1a;
        }
        
        h2 {
            font-size: 1.8em;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #2a2a2a;
        }
        
        h3 {
            font-size: 1.4em;
            margin-top: 1.2em;
            margin-bottom: 0.4em;
            color: #3a3a3a;
        }
        
        p {
            margin-bottom: 1em;
        }
        
        a {
            color: #0066cc;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        
        th {
            background: #f8f8f8;
            font-weight: bold;
        }
        
        .meta-info {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 1px solid #eee;
        }
        
        .internal-links {
            background: #f8f9fa;
            padding: 15px;
            margin: 2em 0;
            border-left: 4px solid #0066cc;
        }
        
        .internal-links h3 {
            margin-top: 0;
        }
    </style>
</head>
<body>
    <article>
        <header>
            <h1>{{ title }}</h1>
            <div class="meta-info">
                Published by <strong>Sendmarc</strong> on {{ date }}
            </div>
        </header>
        
        {{ content|safe }}
        
        {% if internal_links %}
        <aside class="internal-links">
            <h3>Related Resources</h3>
            <ul>
            {% for link in internal_links %}
                <li><a href="#">{{ link }}</a></li>
            {% endfor %}
            </ul>
        </aside>
        {% endif %}
    </article>
</body>
</html>
'''
    
    template = Template(template_str)
    
    rendered = template.render(
        title=metadata.get('title', 'Sendmarc Blog Post'),
        meta_description=metadata.get('meta_description', ''),
        content=html,
        schema_json=json.dumps(schema, indent=2),
        date=datetime.utcnow().strftime('%B %d, %Y'),
        internal_links=metadata.get('internal_links', [])
    )
    
    return rendered


def add_internal_links(html: str, opportunities: list) -> tuple[str, list]:
    """
    Add internal link suggestions to HTML
    
    Args:
        html: HTML content
        opportunities: List of internal link opportunities
        
    Returns:
        Tuple of (modified HTML, list of suggested links)
    """
    # For MVP, we'll just return opportunities to display
    # Full implementation would intelligently insert links
    
    suggested_links = []
    
    for opp in opportunities[:3]:  # Limit to top 3
        suggested_links.append({
            'text': opp,
            'url': f"/blog/{opp.lower().replace(' ', '-')}",
            'utm_params': '?utm_source=blog&utm_medium=internal_link'
        })
    
    return html, suggested_links


def process_images(html: str) -> str:
    """
    Add image placeholders with suggested alt text
    
    Args:
        html: HTML content
        
    Returns:
        HTML with image placeholders
    """
    # For MVP, this is a placeholder
    # In production, would generate/optimize images
    
    return html


def run(
    pipeline_id: str,
    draft_output: Dict[str, Any],
    qa_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Stage 8: HTML Structuring & Production Formatting
    
    Args:
        pipeline_id: Unique pipeline identifier
        draft_output: Output from Stage 6
        qa_output: Output from Stage 7
        
    Returns:
        Stage output dictionary
    """
    try:
        content = draft_output['content']
        metadata = draft_output['metadata']
        
        # Convert markdown to HTML
        html = markdown_to_html(content)
        
        # Validate HTML
        is_valid, issues = validate_html(html)
        if not is_valid:
            print(f"⚠ HTML validation issues: {', '.join(issues)}")
        
        # Generate Schema.org markup
        schema = generate_schema_markup(metadata)
        
        # Add internal link opportunities from QA
        from utils.validation import find_internal_link_opportunities
        text = content.replace('#', '').replace('*', '')
        internal_links = find_internal_link_opportunities(text)
        
        html, suggested_links = add_internal_links(html, internal_links)
        metadata['internal_links'] = internal_links
        
        # Process images (placeholder for MVP)
        html = process_images(html)
        
        # Apply template
        final_html = apply_template(html, metadata, schema)
        
        # Save HTML output
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'outputs'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        html_file = os.path.join(output_dir, f"{pipeline_id}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        # Save metadata separately
        metadata_file = os.path.join(output_dir, f"{pipeline_id}_metadata.json")
        full_metadata = {
            **metadata,
            'schema': schema,
            'internal_links': internal_links,
            'suggested_links': suggested_links
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, indent=2)
        
        print(f"✓ HTML saved to {html_file}")
        print(f"✓ Metadata saved to {metadata_file}")
        
        return {
            'success': True,
            'html_file': html_file,
            'metadata_file': metadata_file,
            'html_preview': final_html[:500] + '...',
            'metadata': full_metadata,
            'validation': {
                'is_valid': is_valid,
                'issues': issues
            }
        }
        
    except Exception as e:
        print(f"Stage 8 failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

