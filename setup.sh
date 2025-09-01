#!/bin/bash
# ===========================================
# BigQuery Analytics Dashboard - Setup Script
# ===========================================
# This script sets up the project for new users
# Ensures Polars is properly installed and configured

echo "🚀 BigQuery Analytics Dashboard Setup"
echo "======================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies (including Polars and BigQuery Storage)..."
pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import polars as pl
    print(f'✅ Polars {pl.__version__} installed successfully!')
except ImportError as e:
    print(f'❌ Polars installation failed: {e}')
    exit(1)

try:
    import streamlit
    print(f'✅ Streamlit {streamlit.__version__} ready!')
except ImportError as e:
    print(f'❌ Streamlit installation failed: {e}')
    exit(1)

try:
    import plotly
    print(f'✅ Plotly {plotly.__version__} ready!')
except ImportError as e:
    print(f'❌ Plotly installation failed: {e}')
    exit(1)

print('\\n🎉 Setup complete! Your dashboard is ready.')
print('\\n📋 Next steps:')
print('1. Configure BigQuery: Edit config/bigquery_config.json')
print('2. Authenticate: gcloud auth application-default login')
print('3. Run dashboard: streamlit run Main.py')
print('\\n⚠️  Remember to always activate the virtual environment:')
print('   source .venv/bin/activate')
"

echo ""
echo "🎯 Setup script completed!"
echo ""
echo "📋 Quick start commands:"
echo "source .venv/bin/activate"
echo "streamlit run Main.py"
