"""
Quick start guide for Reflex development.
"""

# Install requirements
pip install -r requirements.txt

# Run development server
reflex run

# Build for production
reflex export

# Run type checking
mypy yvynation/

# Format code
black yvynation/

# Run linter
flake8 yvynation/

# Run tests
pytest
