#!/bin/bash
# GitHub Setup Commands for Email Productivity Agent

echo "🚀 Setting up GitHub repository..."

# Navigate to project directory
cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"

# Initialize git repository
echo "📦 Initializing git repository..."
git init

# Add all files
echo "➕ Adding files to git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Email Productivity Agent with Streamlit and Gemini AI

Features:
- AI-powered email categorization
- Action item extraction
- Chat interface for inbox queries
- Draft generation and refinement
- Customizable prompts
- Local SQLite database"

# Instructions
echo ""
echo "✅ Git repository initialized and files committed!"
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub: https://github.com/new"
echo "2. Repository name: email-productivity-agent"
echo "3. DO NOT initialize with README (we already have one)"
echo "4. Copy the repository URL"
echo "5. Run these commands:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/email-productivity-agent.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Replace YOUR_USERNAME with your actual GitHub username!"


