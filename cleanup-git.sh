#!/bin/bash

# Git Cleanup Script
# Removes large files from git tracking that should be ignored

echo "=== Git Cleanup Script ==="
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a git repository!"
    exit 1
fi

echo "1. Checking for files that should be ignored..."
echo ""

# Find files that match gitignore patterns but are still tracked
TRACKED_LOGS=$(git ls-files | grep -E "\.log$")
TRACKED_MODELS=$(git ls-files | grep -E "models/.*\.(pkl|h5|pt|pth)")
TRACKED_DATA=$(git ls-files | grep -E "data/(balanced|processed|labeled)/.*\.(jsonl|json)$" | grep -v ".gitkeep")
TRACKED_CACHE=$(git ls-files | grep -E "__pycache__|\.pyc$|\.cache")

# Display what will be removed
if [ -n "$TRACKED_LOGS" ]; then
    echo "Log files to remove from tracking:"
    echo "$TRACKED_LOGS"
    echo ""
fi

if [ -n "$TRACKED_MODELS" ]; then
    echo "Model files to remove from tracking:"
    echo "$TRACKED_MODELS"
    echo ""
fi

if [ -n "$TRACKED_DATA" ]; then
    echo "Large data files to remove from tracking:"
    echo "$TRACKED_DATA"
    echo ""
fi

if [ -n "$TRACKED_CACHE" ]; then
    echo "Cache files to remove from tracking:"
    echo "$TRACKED_CACHE"
    echo ""
fi

# Count total files
TOTAL_COUNT=$(echo -e "$TRACKED_LOGS\n$TRACKED_MODELS\n$TRACKED_DATA\n$TRACKED_CACHE" | grep -v "^$" | wc -l)

if [ "$TOTAL_COUNT" -eq 0 ]; then
    echo "✓ No files need to be removed from tracking!"
    exit 0
fi

echo "Total files to remove: $TOTAL_COUNT"
echo ""
read -p "Do you want to remove these files from git tracking? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "2. Removing files from git tracking (keeping local files)..."
echo ""

# Remove from git but keep local files
if [ -n "$TRACKED_LOGS" ]; then
    echo "$TRACKED_LOGS" | xargs git rm --cached
fi

if [ -n "$TRACKED_MODELS" ]; then
    echo "$TRACKED_MODELS" | xargs git rm --cached
fi

if [ -n "$TRACKED_DATA" ]; then
    echo "$TRACKED_DATA" | xargs git rm --cached
fi

if [ -n "$TRACKED_CACHE" ]; then
    echo "$TRACKED_CACHE" | xargs git rm --cached
fi

echo ""
echo "✓ Files removed from git tracking"
echo ""
echo "3. Summary:"
echo "  - Files are still on your disk"
echo "  - Files will no longer be tracked by git"
echo "  - Run 'git status' to see changes"
echo "  - Commit with: git add .gitignore && git commit -m 'Update gitignore and remove large files from tracking'"
echo ""
