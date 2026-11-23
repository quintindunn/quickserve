@echo off

echo "Creating virtual environment"
py -m venv .venv

call .venv/Scripts/activate

py -m pip install -e .