#!/bin/bash
# Setup script for Git hooks

echo "Setting up Git hooks..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a Git repository"
    exit 1
fi

# Set the hooks path
git config core.hooksPath .githooks

# Make hooks executable
chmod +x .githooks/*

echo "✓ Git hooks configured successfully!"
echo ""
echo "Hooks are now enabled. Prettier will run automatically before each commit."
echo ""
echo "To verify:"
echo "  git config core.hooksPath"
