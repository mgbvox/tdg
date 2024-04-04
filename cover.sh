#!/usr/bin/env zsh

python -m pytest --cov=tdg --cov-report html:htmlcov ./tests

# Check the exit status of pytest
if [[ $? -ne 0 ]]; then
  # Pytest failed, so exit the script
  exit 1
fi

open ./htmlcov/index.html
