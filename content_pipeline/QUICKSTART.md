# Quick Start Guide - 5 Minutes to First Pipeline

## Prerequisites Check

```bash
# Verify Python version (3.8+)
python --version

# Navigate to project
cd "/Users/reshadamin/Downloads/Sendmarc Assessment/content_pipeline"
```

## Step 1: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

Expected output: ~15 packages installed

## Step 2: Configure API Keys (1 minute)

Create `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit with your keys
nano .env  # or use any text editor
```

Add at minimum:
```
GEMINI_API_KEY=your_actual_key_here
```

Optional (for full features):
```
SERPAPI_KEY=your_key_here
JINA_API_KEY=your_key_here
```

### Get API Keys

- **Gemini**: https://makersuite.google.com/app/apikey (Free)
- **SerpAPI**: https://serpapi.com/ (100 free searches/month)
- **Jina AI**: https://jina.ai/ (Free tier)

## Step 3: Initialize System (30 seconds)

```bash
python setup.py
```

Expected output:
```
✓ Environment variables OK
✓ Directories created
✓ Database initialized
✓ Brand voice database initialized
✓ All validation tests passed
✓ Setup Complete!
```

## Step 4: Run Your First Pipeline (1 minute to start)

### Option A: Command Line

```bash
python main.py --url "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/"
```

This will:
1. Extract content from the URL
2. Analyze topics and keywords
3. Check safety/plagiarism
4. Generate original Sendmarc content
5. Score quality
6. Create production HTML

**Expected duration**: 3-8 minutes depending on content length

### Option B: Dashboard (Recommended)

```bash
streamlit run dashboard/app.py
```

Then in browser:
1. Enter URL in sidebar: `https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/`
2. Click "▶️ Run Pipeline"
3. Wait for completion (progress shown)
4. Review in tabs
5. Approve/Reject

## What to Expect

### Successful Pipeline Output

```
############################################################
# Starting Content Intelligence Pipeline
# Pipeline ID: abc123-def456-...
# Source URL: https://...
############################################################

Stage 1: Content Extraction
✓ Jina extraction successful (1250 words)

Stage 2: Content Intelligence Analysis
✓ Content analysis complete
✓ Extracted 8 primary keywords
✓ Identified 4 content gaps

Stage 3: Safety & Ethics Gate
✓ LOW RISK: Standard blog content
✓ GREEN: Safe to proceed

Stage 5: Outline Generation
✓ Outline generated with 5 main sections

Stage 6: Full Draft Generation
✓ Generated article draft (1847 words)

Stage 7: Quality Assurance
✓ Plagiarism check passed (max similarity: 34%)
✓ SEO Score: 78.5/100

Stage 8: HTML Formatting
✓ HTML saved to data/outputs/abc123-def456.html

############################################################
# Pipeline Completed Successfully!
# Status: completed
# Quality Score: 78.5/100
############################################################
```

## Viewing Results

### In Dashboard

1. Click on pipeline in sidebar
2. Navigate through tabs:
   - **Overview**: Pipeline status and metrics
   - **Content**: View generated article
   - **Quality**: SEO scores and checks
   - **Comparison**: Side-by-side with competitor
   - **Stages**: Debug information

### In Files

```bash
# View generated HTML
open data/outputs/<pipeline-id>.html

# View markdown draft
cat data/drafts/<pipeline-id>.md

# View extracted competitor content
cat data/extractions/<pipeline-id>.md
```

## Common First-Run Issues

### Issue: "GEMINI_API_KEY not found"
**Solution**: 
```bash
# Check .env file exists
ls -la .env

# Verify content
cat .env
```

### Issue: "Module not found"
**Solution**:
```bash
# Ensure in correct directory
pwd  # Should end with /content_pipeline

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Pipeline is slow
**Expected**: LLM generation takes 2-5 minutes for stages 5-6
**Check**: Watch terminal for progress updates

### Issue: "Extraction failed"
**Try**:
- Different URL (some sites block scrapers)
- Direct blog post URL (not homepage)
- URLs from these domains work well:
  - cloudflare.com/learning
  - mailgun.com/blog
  - proofpoint.com/us/blog

## Test URLs (Known to Work)

```bash
# DMARC explainer
python main.py --url "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/"

# Email authentication
python main.py --url "https://www.mailgun.com/blog/email/what-is-dmarc/"

# Phishing prevention
python main.py --url "https://www.proofpoint.com/us/blog/email-security/dmarc-compliance"
```

## Next Steps

1. **Explore Dashboard**: Run `streamlit run dashboard/app.py`
2. **Review Generated Content**: Check quality scores and HTML output
3. **Add Brand Voice**: Place Sendmarc blogs in `data/sendmarc_blogs/`
4. **Customize Prompts**: Edit `config/prompts.yaml`
5. **Adjust SEO Rules**: Modify `config/seo_rules.yaml`

## CLI Commands Reference

```bash
# Run pipeline
python main.py --url <url>

# List recent pipelines
python main.py --list

# View specific pipeline
python main.py --load <pipeline-id>

# Initialize database
python main.py --setup-db

# Setup brand voice
python main.py --setup-rag

# Run tests
python setup.py --test

# Launch dashboard
streamlit run dashboard/app.py
```

## Getting Help

1. Check `README.md` for detailed documentation
2. Review `config/` files for customization options
3. Check database: `sqlite3 data/pipeline.db` then `SELECT * FROM pipelines;`
4. View logs in terminal output
5. Inspect stage outputs in dashboard "Stages" tab

## Success Checklist

After first pipeline completes, verify:

- [x] No errors in terminal
- [x] Pipeline status shows "completed" or "review_required"
- [x] Quality score >70/100
- [x] Plagiarism similarity <85%
- [x] HTML file exists in `data/outputs/`
- [x] Content reads naturally
- [x] Sendmarc brand voice maintained

## Time Budget

- **Setup**: 3-4 minutes
- **First pipeline**: 5-8 minutes
- **Review in dashboard**: 2-3 minutes
- **Total**: ~15 minutes to fully operational system

---

**Ready to go?** Run `streamlit run dashboard/app.py` and start creating content! 🚀

