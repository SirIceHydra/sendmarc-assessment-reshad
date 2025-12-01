# API Keys Setup Guide

## Required API Keys

### 1. Google Gemini API Key (REQUIRED) ⚠️

**Why**: Used for all LLM tasks (content analysis, outline generation, article writing, fact checking)

**How to get it**:
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

**Free Tier**: 1500 requests/day (plenty for MVP testing)

**Where to put it**: In `.env` file as `GEMINI_API_KEY=your_key_here`

---

### 2. SerpAPI Key (OPTIONAL) 

**Why**: Used for keyword research and SEO analysis in Stage 2

**How to get it**:
1. Go to: https://serpapi.com/
2. Sign up for free account
3. Go to Dashboard → API Keys
4. Copy your API key

**Free Tier**: 100 searches/month

**Where to put it**: In `.env` file as `SERPAPI_KEY=your_key_here`

**Note**: Pipeline will work without this, but keyword research will be limited

---

### 3. Jina AI Reader API Key (OPTIONAL)

**Why**: Used for clean content extraction from URLs in Stage 1

**How to get it**:
1. Go to: https://jina.ai/
2. Sign up for free account
3. Navigate to API Keys section
4. Copy your key

**Free Tier**: Generous limits

**Where to put it**: In `.env` file as `JINA_API_KEY=your_key_here`

**Note**: Pipeline will automatically fallback to Trafilatura (local, no API needed) if not provided

---

## Quick Setup Steps

1. **Create `.env` file**:
   ```bash
   cd "/Users/reshadamin/Downloads/Sendmarc Assessment/content_pipeline"
   cp .env.example .env
   ```

2. **Edit `.env` file** with your keys:
   ```bash
   nano .env
   # or use any text editor
   ```

3. **Minimum required**: Just `GEMINI_API_KEY` (others are optional)

4. **Verify setup**:
   ```bash
   python setup.py
   ```

---

## Example `.env` File

```bash
# Minimum setup (just Gemini)
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Full setup (all APIs)
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SERPAPI_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Testing Your Keys

After setting up `.env`, test with:

```bash
python setup.py --test
```

This will verify:
- ✅ All required keys are present
- ✅ Database can be initialized
- ✅ Modules can be imported

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure `.env` file exists in `content_pipeline/` directory
- Check the key is on a single line (no line breaks)
- Verify no extra spaces around the `=` sign

### "API call failed"
- Check your API key is correct
- Verify you haven't exceeded free tier limits
- Check internet connection

### "Module not found"
- Run: `pip install -r requirements.txt`
- Make sure you're in the correct directory

---

## Cost Summary

**MVP Testing (Free Tier)**:
- Gemini: $0.00 (1500 requests/day free)
- SerpAPI: $0.00 (100 searches/month free)
- Jina AI: $0.00 (generous free tier)
- **Total Cost: $0.00** ✅

**Per Pipeline Usage**:
- Gemini: ~6 API calls (analysis, outline, draft, fact-check)
- SerpAPI: ~5 searches (if enabled)
- Jina AI: 1 call (if enabled)
- **All within free tier limits!**

