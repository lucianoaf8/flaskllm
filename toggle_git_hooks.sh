#!/bin/bash

# Script to toggle Git hooks on and off
# Usage: ./toggle_git_hooks.sh [on|off]

HOOKS_PATH=".git/hooks"
HOOKS_BACKUP_PATH="$HOME/hooks_backup"

# Create backup directory if it doesn't exist
mkdir -p "$HOOKS_BACKUP_PATH"

# Function to enable hooks
enable_hooks() {
  if [ -f "$HOOKS_BACKUP_PATH/pre-commit" ]; then
    cp "$HOOKS_BACKUP_PATH/pre-commit" "$HOOKS_PATH/"
    chmod +x "$HOOKS_PATH/pre-commit"
    echo "Git hooks enabled."
  else
    echo "No backup hooks found. Cannot enable."
  fi
}

# Function to disable hooks
disable_hooks() {
  if [ -f "$HOOKS_PATH/pre-commit" ]; then
    # Backup if not already backed up
    if [ ! -f "$HOOKS_BACKUP_PATH/pre-commit" ]; then
      cp "$HOOKS_PATH/pre-commit" "$HOOKS_BACKUP_PATH/"
    fi
    # Remove the hook
    rm "$HOOKS_PATH/pre-commit"
    echo "Git hooks disabled."
  else
    echo "No hooks found to disable."
  fi
}

# Main script logic
if [ "$1" = "on" ]; then
  enable_hooks
elif [ "$1" = "off" ]; then
  disable_hooks
else
  echo "Usage: $0 [on|off]"
  echo "  on  - Enable Git hooks"
  echo "  off - Disable Git hooks"
fi
