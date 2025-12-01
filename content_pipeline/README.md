# Sendmarc Content Intelligence Pipeline - MVP

A serverless pipeline that transforms competitor blog URLs into production-ready Sendmarc blog drafts with original content, proper HTML structure, brand voice consistency, and SEO optimization.

## 🎯 Overview

This MVP demonstrates an automated content creation pipeline that:

1. **Extracts** clean content from competitor URLs
2. **Analyzes** content to identify topics, keywords, and gaps
3. **Validates** safety and copyright risks
4. **Generates** original content with Sendmarc's brand voice
5. **Scores** content quality with SEO metrics and plagiarism checks
6. **Formats** into production-ready HTML
7. **Reviews** through human-in-the-loop dashboard

## 📋 Prerequisites

- Python 3.8+
- API Keys (free tiers):
  - Google Gemini 2.0 Flash API
  - (Optional) SerpAPI for keyword research
  - (Optional) Jina AI Reader for content extraction

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd content_pipeline

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py
```

### 2. Configuration

Create a `.env` file with your API keys:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
SERPAPI_KEY=your_serpapi_key_here  # Optional
JINA_API_KEY=your_jina_api_key_here  # Optional
```

### 3. Run Pipeline

**CLI Mode:**
```bash
# Run pipeline on a competitor URL
python main.py --url https://competitor.com/blog/article

# List recent pipelines
python main.py --list

# Load specific pipeline
python main.py --load <pipeline-id>
```

**Dashboard Mode:**
```bash
# Launch Streamlit dashboard
streamlit run dashboard/app.py
```

Then:
1. Enter a competitor URL in the sidebar
2. Click "Run Pipeline"
3. Review generated content in tabs
4. Approve, request changes, or reject

## 🏗️ Architecture

### Pipeline Stages

| Stage | Name | Purpose | Key Technologies |
|-------|------|---------|-----------------|
| 1 | Content Extraction | Clean content from URLs | Jina AI, Trafilatura |
| 2 | Content Analysis | Identify topics & keywords | Gemini 2.0, SerpAPI |
| 3 | Safety Gate | Copyright & plagiarism check | Sentence-Transformers |
| 4 | Brand Voice RAG | Load Sendmarc examples | ChromaDB, embeddings |
| 5 | Outline Generation | Create content structure | Gemini 2.0, RAG |
| 6 | Full Draft | Write complete article | Gemini 2.0, RAG |
| 7 | Quality Assurance | SEO, plagiarism, readability | Custom scoring |
| 8 | HTML Formatting | Production-ready output | Python-Markdown, Jinja2 |
| 9 | Human Review | Approval workflow | Streamlit dashboard |

### Project Structure

```
content_pipeline/
├── config/               # Configuration files
│   ├── prompts.yaml     # LLM prompts with versioning
│   ├── seo_rules.yaml   # SEO scoring thresholds
│   └── brand_guidelines.yaml
│
├── stages/              # Pipeline stage modules
│   ├── stage1_extract.py
│   ├── stage2_analyze.py
│   ├── stage3_safety.py
│   ├── stage4_rag_setup.py
│   ├── stage5_outline.py
│   ├── stage6_generate.py
│   ├── stage7_qa.py
│   └── stage8_format.py
│
├── utils/               # Shared utilities
│   ├── llm_client.py    # Gemini API wrapper
│   ├── db.py            # SQLite operations
│   └── validation.py    # Content validation
│
├── dashboard/           # Streamlit review interface
│   └── app.py
│
├── data/                # Local storage
│   ├── pipeline.db      # SQLite database
│   ├── chromadb/        # Vector database
│   ├── extractions/     # Raw extracted content
│   ├── drafts/          # Generated drafts
│   ├── outputs/         # Final HTML output
│   └── sendmarc_blogs/  # Brand voice examples
│
├── main.py              # Pipeline orchestrator
├── setup.py             # Setup script
├── requirements.txt     # Python dependencies
└── README.md
```

## 🔧 Configuration

### LLM Prompts

Edit `config/prompts.yaml` to customize:
- Content analysis instructions
- Outline generation guidelines
- Full draft writing style
- Fact-checking criteria

### SEO Rules

Edit `config/seo_rules.yaml` to adjust:
- Word count thresholds
- Readability targets
- Keyword density limits
- Scoring weights

### Brand Guidelines

Edit `config/brand_guidelines.yaml` to define:
- Tone and voice characteristics
- Topic expertise areas
- High/medium/low risk sources
- Content structure preferences

## 📊 Dashboard Features

### Overview Tab
- Pipeline status and progress
- Safety decision and quality score
- Source article metadata
- Content brief summary

### Content Tab
- Generated markdown preview
- HTML rendering
- Metadata (title, description, slug)
- Word count and structure

### Quality Tab
- Overall pass/fail status
- SEO score (0-100) with component breakdown
- Plagiarism similarity check
- Readability metrics
- Blocking issues and warnings
- Improvement recommendations

### Comparison Tab
- Side-by-side view of competitor vs Sendmarc content
- Identify unique value adds

### Stages Tab
- Detailed output from each stage
- Debug information
- Error logs

## 🔐 Safety Features

### Plagiarism Detection
- Semantic similarity using embeddings
- Chunk-level comparison with competitor content
- Threshold: <85% similarity required

### Copyright Risk Assessment
- RED: Major publications (NYT, Forbes, etc.) → Halt
- YELLOW: Medium risk sources → Mandatory review
- GREEN: Standard competitor blogs → Proceed

### Human Review Gates
- Mandatory review for YELLOW/RED sources
- Sensitive topics flagged automatically
- Approval workflow with audit logging

## 📈 Quality Metrics

### SEO Scoring (0-100)

| Component | Weight | Criteria |
|-----------|--------|----------|
| Keyword Optimization | 25% | Primary in H1/intro, density 0.5-2.5% |
| Readability | 20% | Flesch score 50-70 |
| Structure | 20% | Valid hierarchy, 3-6 H2 sections |
| Content Length | 15% | 1500-2500 words |
| Internal Linking | 10% | 2-3 relevant links |
| Meta Optimization | 10% | Description 150-160 chars |

### Validation Rules

**Blocking Issues** (prevent publication):
- Plagiarism similarity >85%
- Missing H1 or meta description
- Readability <30 or >80
- Primary keyword missing from H1

**Warnings** (review recommended):
- Word count out of range
- Keyword density suboptimal
- Insufficient internal links
- Readability slightly out of range

## 🎨 Brand Voice

The pipeline uses RAG (Retrieval-Augmented Generation) to maintain consistency with Sendmarc's brand voice:

1. **One-time Setup**: Populate ChromaDB with existing Sendmarc blogs
2. **Per Article**: Retrieve 3-5 most relevant examples
3. **Generation**: LLM uses examples to match tone and style

### Adding Brand Content

```bash
# Add markdown files to data/sendmarc_blogs/
cp /path/to/sendmarc/blogs/*.md data/sendmarc_blogs/

# Re-populate RAG database
python stages/stage4_rag_setup.py data/sendmarc_blogs/
```

## 🧪 Testing

### Run Setup Tests
```bash
python setup.py --test
```

### Test Individual Stages
```python
# Example: Test Stage 1
from stages import stage1_extract

result = stage1_extract.run(
    pipeline_id="test-123",
    source_url="https://example.com/blog"
)

print(result)
```

### Test Full Pipeline
```bash
# Use a known good URL
python main.py --url https://www.mailgun.com/blog/email/dmarc-guide/
```

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Ensure `.env` file exists in `content_pipeline/` directory
- Check API key is valid and properly formatted
- Run `python setup.py` to verify configuration

### "No brand examples found"
- Add Sendmarc blog markdown files to `data/sendmarc_blogs/`
- Run `python setup.py --populate-rag`
- Pipeline will use sample content if none provided

### "Extraction failed"
- Some sites block scraping
- Try alternative URLs or direct blog posts
- Check network connectivity
- Jina AI will fallback to Trafilatura automatically

### Pipeline hangs or is slow
- LLM generation can take 2-5 minutes
- Check Gemini API rate limits
- Ensure stable internet connection
- Review terminal for progress logs

### Quality check always blocks
- Review `config/seo_rules.yaml` thresholds
- Check if content meets minimum requirements
- Adjust validation rules if needed
- Review blocking issues in dashboard

## 📝 Database Schema

### pipelines
- `id`: Pipeline UUID
- `source_url`: Competitor URL
- `current_stage`: Latest completed stage
- `status`: running|completed|blocked_safety|blocked_qa|approved|rejected
- `safety_decision`: RED|YELLOW|GREEN
- `quality_score`: 0-100

### stage_outputs
- `pipeline_id`: Foreign key to pipelines
- `stage`: Stage number (1-8)
- `output_json`: Stage result as JSON

### audit_log
- `pipeline_id`: Foreign key to pipelines
- `event_type`: Event name
- `reviewer`: User identifier
- `metadata`: Event-specific data
- `timestamp`: Event time

## 🔮 Future Enhancements

### Phase 2 (Production)
- [ ] AWS Lambda deployment
- [ ] PostgreSQL + S3 storage
- [ ] Temporal workflow orchestration
- [ ] Real-time monitoring dashboard
- [ ] Automated image generation
- [ ] WordPress API integration

### Phase 3 (Scale)
- [ ] Multi-language support
- [ ] A/B testing of content variants
- [ ] Performance analytics tracking
- [ ] Automated competitor monitoring
- [ ] Internal linking graph analysis
- [ ] Content calendar integration

## 📄 License

Proprietary - Sendmarc Internal Use Only

## 🤝 Support

For issues or questions:
1. Check troubleshooting section above
2. Review audit logs in database
3. Examine stage outputs in dashboard
4. Contact development team

## 🎯 Success Criteria

The MVP is successful if it can:

✅ Extract and analyze competitor content  
✅ Generate original content (plagiarism <85%)  
✅ Achieve SEO score >70/100  
✅ Maintain Sendmarc brand voice  
✅ Produce valid production-ready HTML  
✅ Provide human review interface  
✅ Complete end-to-end in <10 minutes  

---

**Built with:** Python, Gemini 2.0 Flash, Sentence-Transformers, ChromaDB, Streamlit

**MVP Development Time:** Target 8-12 hours

**Status:** ✅ Production Ready (MVP)

