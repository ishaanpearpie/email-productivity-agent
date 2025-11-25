# Deployment Guide - Email Productivity Agent

## 📝 Recommended GitHub Repository Name

**Suggested names:**
1. `email-productivity-agent` ⭐ (Recommended - clear and professional)
2. `ai-email-assistant`
3. `streamlit-email-agent`
4. `gemini-email-agent`

---

## 🚀 Step 1: GitHub Setup & Push

### A. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `email-productivity-agent`
3. Description: `AI-powered email management system built with Streamlit and Google Gemini`
4. Visibility: Public or Private (your choice)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### B. Push Code to GitHub

```bash
# Navigate to project directory
cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Email Productivity Agent with Streamlit and Gemini AI"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/email-productivity-agent.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note:** If you haven't set up GitHub authentication, you may need to:
- Use GitHub CLI: `gh auth login`
- Or use SSH: `git remote add origin git@github.com:YOUR_USERNAME/email-productivity-agent.git`
- Or use Personal Access Token in the URL

---

## 🌐 Step 2: Deployment Options

### ⚠️ Important Note About Vercel

**Vercel is NOT recommended for Streamlit apps** because:
- Vercel is optimized for static sites and serverless functions
- Streamlit requires a persistent Python server
- Better alternatives exist that support Streamlit natively

### ✅ Recommended Deployment Platforms

#### Option 1: Streamlit Cloud (BEST for Streamlit) ⭐

**Advantages:**
- Free tier available
- Built specifically for Streamlit
- Easy deployment from GitHub
- Automatic HTTPS
- Custom domains supported

**Steps:**
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `email-productivity-agent`
5. Main file path: `app.py`
6. Branch: `main`
7. **Important:** Add secrets for environment variables:
   - Go to "Advanced settings"
   - Add secret: `GEMINI_API_KEY` with your API key value
   - Add other config if needed (or use defaults)
8. Click "Deploy"
9. Your app will be live at: `https://your-app-name.streamlit.app`

**Environment Variables in Streamlit Cloud:**
```
GEMINI_API_KEY=AIzaSyD7MC-qgoylfePdL1a6XGUKlLEbbV8BQn0
GEMINI_MODEL=gemini-1.5-flash
DATABASE_PATH=./data/email_agent.db
```

#### Option 2: Railway

**Steps:**
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect Python
6. Add environment variables in Railway dashboard:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-1.5-flash`
7. Add start command: `streamlit run app.py --server.port $PORT`
8. Deploy

**Required files for Railway:**

Create `Procfile`:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

#### Option 3: Render

**Steps:**
1. Go to https://render.com
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Connect your repository
5. Settings:
   - Name: `email-productivity-agent`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
6. Add environment variables:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-1.5-flash`
7. Click "Create Web Service"

**Required files for Render:**

Create `Procfile`:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

---

## 🔧 If You Still Want to Try Vercel

**Note:** This is NOT recommended and may not work properly. Vercel doesn't natively support Streamlit.

### Vercel Configuration (Experimental)

You would need to:
1. Create a serverless function wrapper
2. This is complex and not recommended
3. Better to use Streamlit Cloud instead

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] `.env` file is in `.gitignore` (already done ✓)
- [ ] `.env.example` exists with placeholder values (already done ✓)
- [ ] No API keys in code (already done ✓)
- [ ] `requirements.txt` is complete (already done ✓)
- [ ] README.md has deployment instructions (update if needed)

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use environment variables** on hosting platform
3. **Rotate API keys** if accidentally exposed
4. **Use secrets management** on your hosting platform

---

## 📝 Quick Commands Summary

```bash
# Navigate to project
cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"

# Initialize and push to GitHub
git init
git add .
git commit -m "Initial commit: Email Productivity Agent"
git remote add origin https://github.com/YOUR_USERNAME/email-productivity-agent.git
git branch -M main
git push -u origin main

# For future updates
git add .
git commit -m "Your commit message"
git push
```

---

## 🎯 Recommended Deployment Flow

1. **Push to GitHub** (use commands above)
2. **Deploy on Streamlit Cloud** (easiest and best for Streamlit)
3. **Share your live URL** with others!

---

## 📞 Need Help?

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs

**Best of luck with your deployment! 🚀**


