#!/bin/bash
set -e

# Install pre-commit hooks if .git directory exists and hooks are not installed
if [ -d ".git" ] && [ ! -f ".git/hooks/pre-commit" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# Run the main command
exec "$@"

