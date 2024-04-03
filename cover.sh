#!/usr/bin/env zsh

python -m pytest --cov=tdg --cov-report html:htmlcov ./tests

open ./htmlcov/index.html