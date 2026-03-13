# Google Gemini API Setup Guide - Learning Path Generation

## Why Gemini API?

Your skill gap analysis system now integrates Google's Gemini AI to generate **personalized, intelligent learning paths** instead of generic rule-based timelines.

**Benefits:**
- ✅ Specific course recommendations (not generic "take a course")
- ✅ Realistic time estimates based on your availability
- ✅ Smart prerequisite detection
- ✅ Free tier: 15 requests/minute, 1500 requests/day
- ✅ No credit card required
- ✅ Graceful fallback to rule-based paths if API unavailable

---

## Step 1: Get Your Free API Key

### 1.1 Navigate to Google AI Studio
- Go to: **https://aistudio.google.com/app/apikey**
- Sign in with your Google account (create one if needed - it's free)

### 1.2 Create API Key
- Click **"Create API Key"** button
- Select **"Create API key in new project"**
- Copy the generated API key (looks like: `AIzaSyD...`)

### 1.3 Create .env File
In your project root directory (E:\AI-FAIR_PROJECT), create a file named `.env`:

```
GEMINI_API_KEY=your_api_key_here_paste_your_key
```

Replace `your_api_key_here_paste_your_key` with the actual key you copied.

**Important:** This file is already in `.gitignore`, so it won't be committed to version control.

---

## Step 2: Test the Setup

Run this command to verify the API key works:

```bash
python debug_learning_path.py
```

**Expected output:**
```
✓ Gemini API initialized successfully
✓ LLM-powered learning paths enabled (Gemini API)
✓ Full analysis complete with all components
```

---

## Step 3: Run the Application

Now you can start the Streamlit app:

```bash
streamlit run streamlit_app.py
```

### Using the Enhanced Learning Paths

1. **Upload Resume** → Select your PDF/DOCX/TXT resume
2. **Set Learning Preferences** (in sidebar):
   - Experience Level: beginner/intermediate/advanced
   - Time Available: part-time (2hrs/day) / full-time (6-8hrs/day) / minimal (1hr/day)
   - Learning Style: hands-on (projects) / theory-first (courses) / mixed
   - Budget: free only / budget-friendly / willing to invest
3. **Click "Analyse Resume"**
4. **View "Skill Gaps" Tab** → See 4 detailed views:
   - **Priority Ranking** - Top 10 skills by 4-factor scoring
   - **Learning Path** - Month-by-month milestones with specific resources
   - **Quick Wins** - Easy, high-impact skills to learn first
   - **Gap Breakdown** - Categorized visualization

---

## What You'll See

### Example Learning Path Output

**Month 1: Docker Fundamentals** ┈ CRITICAL Priority
- Week 1-4
- Time: 8 hours/week
- Difficulty: Easy
- 📚 Resources:
  - Docker for Beginners (YouTube) - free
  - Official Docker Docs - free
- 🛠️ Projects:
  - Containerize a Python Flask app
  - Create multi-container app with Docker Compose
- ✅ Success Criteria:
  - Can write Dockerfiles from scratch
  - Deployed 2 containerized projects
- Match Score: 75% → 78% (+3%)

---

## Fallback Behavior

If the API key is invalid or network is down:
- System automatically falls back to rule-based learning paths
- Still shows month-by-month timeline
- Less detailed but fully functional
- Console shows: "Using fallback learning path..."

---

## API Rate Limits

**Free Tier (No Credit Card):**
- 15 requests per minute
- 1,500 requests per day

**Fair-Path Usage:**
- 1 learning path = 1 API call
- With caching, repeated analyses = 0 API calls
- 1 hour of user interactions ≈ 2-5 API calls
- You can handle 100+ users/day easily

**If you hit limits:**
- System gracefully falls back to rule-based paths
- No errors shown to users
- Resume analysis still completes

---

## Troubleshooting

### Issue: "API key expired"
**Solution:** Get a new API key from https://aistudio.google.com/app/apikey and update `.env`

### Issue: "GEMINI_API_KEY not found"
**Solution:** Make sure `.env` file exists in project root with format:
```
GEMINI_API_KEY=your_actual_key_here
```

### Issue: "Rate limit exceeded"
**Solution:** Wait a minute before next request, or system will use fallback automatically

### Issue: "Connection error"
**Solution:** Check internet connection. System will use fallback paths automatically.

### Issue: "Gemini not available" (using rule-based instead)
**Solution:** This is expected if:
- No `.env` file
- Invalid API key
- Network unreachable
- API changed
→ System still works with rule-based paths!

---

## Upgrading to Paid Plan (Optional)

If you want more requests:
1. Go to: https://aistudio.google.com/pricing
2. Set up billing
3. Get higher limits:
   - Up to 1,500 requests per minute
   - No daily limit
   - Still very affordable ($0.075/1M input tokens)

---

## File locations

- `.env` - API key (git-ignored) - **ROOT DIRECTORY**
- `.env.example` - Example template - ROOT DIRECTORY
- `src/llm_learning_path_generator.py` - LLM integration - NEW FILE
- `src/skill_gap_analysis.py` - Modified to support LLM
- `streamlit_app.py` - Enhanced UI with learning preferences
- `debug_learning_path.py` - Debug/test script

---

## Questions?

If the system shows only rule-based paths:
1. Run: `python debug_learning_path.py` to see what's happening
2. Check console output for error messages
3. Verify `.env` file exists and has correct format
4. System still works perfectly without Gemini!

---

## Next Steps

1. ✅ Install dependencies (already done)
2. Get free API key from https://aistudio.google.com/app/apikey
3. Create `.env` file with GEMINI_API_KEY
4. Run: `python final_verification.py`
5. Run: `streamlit run streamlit_app.py`
6. Enjoy personalized AI learning paths! 🚀

