# 🚀 Complete Setup Guide - Get Running in 5 Minutes

## Step 1: Install Dependencies ✅

**Already done!** Virtual environment created and dependencies installed.

**To activate the virtual environment in the future:**
```bash
cd "/Users/reshadamin/Downloads/Sendmarc Assessment/content_pipeline"
source venv/bin/activate
```

---

## Step 2: Get API Keys 🔑

### **REQUIRED: Google Gemini API Key** ⚠️

**You MUST have this to run the pipeline!**

1. **Go to**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click** "Create API Key" or "Get API Key"
4. **Copy** the key (looks like: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Free Tier**: 1500 requests/day (more than enough for testing)

---

### **OPTIONAL: SerpAPI Key** (for better keyword research)

1. **Go to**: https://serpapi.com/
2. **Sign up** for free account
3. **Dashboard** → Copy your API key
4. **Free Tier**: 100 searches/month

**Note**: Pipeline works without this, but keyword research will be limited.

---

### **OPTIONAL: Jina AI Reader Key** (for better content extraction)

1. **Go to**: https://jina.ai/
2. **Sign up** for free account
3. **Get** your API key
4. **Free Tier**: Generous limits

**Note**: Pipeline automatically falls back to local extraction if not provided.

---

## Step 3: Create `.env` File 📝

**Create the file:**
```bash
cd "/Users/reshadamin/Downloads/Sendmarc Assessment/content_pipeline"
nano .env
```

**Add your keys** (minimum: just Gemini):
```bash
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SERPAPI_KEY=your_serpapi_key_here
JINA_API_KEY=your_jina_api_key_here
```

**Or use a text editor** (VS Code, TextEdit, etc.) to create `.env` in the `content_pipeline` folder.

---

## Step 4: Initialize the System 🛠️

**Run the setup script:**
```bash
source venv/bin/activate
python setup.py
```

**Expected output:**
```
✓ Environment variables OK
✓ Directories created
✓ Database initialized
✓ Brand voice database initialized
✓ All validation tests passed
✓ Setup Complete!
```

---

## Step 5: Run Your First Pipeline! 🎉

### Option A: Command Line

```bash
source venv/bin/activate
python main.py --url "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/"
```

**This will:**
1. Extract content from the URL
2. Analyze topics and keywords
3. Check safety/plagiarism
4. Generate original Sendmarc content
5. Score quality
6. Create production HTML

**Duration**: 3-8 minutes

---

### Option B: Dashboard (Recommended) 🖥️

```bash
source venv/bin/activate
streamlit run dashboard/app.py
```

**Then in your browser:**
1. Enter URL in sidebar
2. Click "▶️ Run Pipeline"
3. Wait for completion
4. Review in tabs
5. Approve/Reject

---

## 📋 Quick Reference

### Activate Virtual Environment
```bash
cd "/Users/reshadamin/Downloads/Sendmarc Assessment/content_pipeline"
source venv/bin/activate
```

### Run Pipeline (CLI)
```bash
python main.py --url "https://example.com/blog/article"
```

### Launch Dashboard
```bash
streamlit run dashboard/app.py
```

### List Recent Pipelines
```bash
python main.py --list
```

### View Specific Pipeline
```bash
python main.py --load <pipeline-id>
```

---

## 🧪 Test URLs (Known to Work)

```bash
# DMARC guide
python main.py --url "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/"

# Email authentication
python main.py --url "https://www.mailgun.com/blog/email/what-is-dmarc/"

# Phishing prevention
python main.py --url "https://www.proofpoint.com/us/blog/email-security/dmarc-compliance"
```

---

## ❓ Troubleshooting

### "GEMINI_API_KEY not found"
- ✅ Check `.env` file exists in `content_pipeline/` directory
- ✅ Verify key is on single line (no breaks)
- ✅ No extra spaces around `=`

### "Module not found"
- ✅ Activate virtual environment: `source venv/bin/activate`
- ✅ Reinstall: `pip install -r requirements.txt`

### "API call failed"
- ✅ Check internet connection
- ✅ Verify API key is correct
- ✅ Check you haven't exceeded free tier limits

### Pipeline is slow
- ✅ Normal! LLM generation takes 2-5 minutes
- ✅ Watch terminal for progress updates

---

## 📊 What You'll Get

After pipeline completes:

1. **HTML File**: `data/outputs/<pipeline-id>.html`
2. **Markdown Draft**: `data/drafts/<pipeline-id>.md`
3. **Quality Report**: In dashboard or database
4. **Metadata**: `data/outputs/<pipeline-id>_metadata.json`

---

## ✅ Success Checklist

After first pipeline:
- [ ] No errors in terminal
- [ ] Pipeline status: "completed" or "review_required"
- [ ] Quality score >70/100
- [ ] Plagiarism similarity <85%
- [ ] HTML file exists
- [ ] Content reads naturally

---

## 🎯 Next Steps

1. **Get Gemini API key** (required)
2. **Create `.env` file** with your key
3. **Run setup**: `python setup.py`
4. **Test pipeline**: Use one of the test URLs above
5. **Review in dashboard**: `streamlit run dashboard/app.py`

**Ready? Let's go!** 🚀

