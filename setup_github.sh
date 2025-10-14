#!/bin/bash

# GitHub Repository Setup Script
# Run this after creating your GitHub repository

echo "================================================================================
GITHUB REPOSITORY SETUP
================================================================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Run 'git init' first."
    exit 1
fi

# Get repository URL from user
echo "Enter your GitHub repository URL:"
echo "Example: https://github.com/yourusername/umushroom-pead-trading-system.git"
read -p "Repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No repository URL provided."
    exit 1
fi

echo ""
echo "Setting up GitHub remote..."

# Add remote
git remote add origin "$REPO_URL"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

# Verify connection
echo ""
echo "Verifying connection..."
git remote -v

echo ""
echo "✅ GitHub repository connected successfully!"
echo ""
echo "Your repository is now ready for background agents."
echo "Repository URL: $REPO_URL"
