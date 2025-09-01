# BigQuery Analytics Dashboard

A modern analytics dashboard using Streamlit to visualize BigQuery data with interactive charts and business intelligence.

## ⚡ Performance Optimized with Polars

This dashboard has been fully migrated from pandas to **Polars** for significantly improved performance:

- 🚀 **Faster Data Processing** - Columnar format and query optimization
- 💾 **Lower Memory Usage** - Efficient memory management
- ⚡ **Parallel Processing** - Automatic parallelization
- 🔧 **Better Type Safety** - Strict typing system
- 📊 **Optimized Analytics** - Native support for complex aggregations

**⚠️ IMPORTANT:** This project uses Polars, not pandas. Make sure to follow the installation steps below.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- Google Cloud account with BigQuery access
- Git (for cloning the repository)

### 1. Setup Environment
```bash
# Option A: Manual setup (Linux/Mac)
git clone <repository-url>
cd M2Project-MarketingVisualisation
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Option B: Automated setup (Recommended for new users)
git clone <repository-url>
cd M2Project-MarketingVisualisation

# Linux/Mac users:
./setup.sh

# Windows users:
setup.bat
```

### 2. Install Dependencies
```bash
# Install all required packages (includes Polars)
pip install -r requirements.txt

# Verify Polars installation
python -c "import polars as pl; print(f'Polars {pl.__version__} ready!')"
```

### 3. Setup Google Cloud Authentication
```bash
# Login to Google Cloud
gcloud auth application-default login
```

### 4. Configure Project
Edit `config/bigquery_config.json` with your BigQuery project details:
```json
{
  "project_id": "your-project-id",
  "dataset_id": "your-dataset-id"
}
```

### 5. Launch Dashboard
```bash
# Linux/Mac - Activate virtual environment
source .venv/bin/activate

# Windows - Activate virtual environment
.venv\Scripts\activate.bat

# Start the dashboard (works on all platforms)
streamlit run Main.py
```

### 6. Access Dashboard
Open your browser to: **http://localhost:8501**

## 📁 Project Structure

```
├── Main.py                      # Core dashboard application
├── utils/                       # Utility modules
│   ├── database.py              # BigQuery operations (Polars DataFrames)
│   ├── visualizations.py        # Chart functions
│   ├── data_processing.py       # Business analytics (Polars optimized)
│   └── performance.py           # Performance monitoring
├── pages/                       # Analytics pages (all Polars-powered)
│   ├── 1_👥_Customer_Analytics.py
│   ├── 2_🛒_Order_Analytics.py
│   ├── 3_⭐_Review_Analytics.py
│   └── 4_🗺️_Geographic_Analytics.py
├── config/
│   └── bigquery_config.json    # BigQuery configuration
└── requirements.txt             # Dependencies (Polars included)
```

## 📊 Dashboard Features

### 👥 Customer Analytics
- RFM customer segmentation with business insights
- Geographic performance analysis
- Customer lifetime value calculations

### 🛒 Order Analytics
- Order trends and delivery performance
- Revenue analysis and order value insights
- Status monitoring and fulfillment tracking

### ⭐ Review Analytics
- Customer satisfaction and sentiment analysis
- Rating trends and category performance
- Time-based review patterns

### 🗺️ Geographic Analytics
- Interactive Brazil map visualization
- State and city performance metrics
- Regional market insights

## ⚙️ Configuration

### BigQuery Setup
1. Create a Google Cloud Project with BigQuery enabled
2. Update `config/bigquery_config.json`:
   ```json
   {
     "project_id": "your-gcp-project-id",
     "dataset_id": "your-bigquery-dataset"
   }
   ```

### Virtual Environment (Required)
Always activate the virtual environment before running:
```bash
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

## 🔧 Troubleshooting

### Quick Fix for New Users
If you're having trouble getting started, run the automated setup script:
```bash
# Linux/Mac
./setup.sh

# Windows
setup.bat
```
This will handle virtual environment creation, dependency installation, and verification automatically.

### Common Issues

**❌ ModuleNotFoundError: No module named 'polars'**
```bash
# Solution 1: Run setup script
# Linux/Mac:
./setup.sh
# Windows:
setup.bat

# Solution 2: Manual fix
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**❌ Virtual environment issues**
```bash
# Recreate virtual environment
# Linux/Mac:
rm -rf .venv
python -m venv .venv
source .venv/bin/activate

# Windows:
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate.bat

pip install -r requirements.txt
```

**❌ Google Cloud Authentication Error**
```bash
# Solution: Re-authenticate
gcloud auth application-default login
```

**❌ Streamlit not starting**
```bash
# Solution: Check virtual environment and dependencies
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.bat

python -c "import streamlit, polars, plotly; print('All good!')"
streamlit run Main.py
```

## 📊 Available Data (Olist E-commerce)

- **Customer data**: Demographics and location (99,441 rows)
- **Order data**: Purchase history and status (99,441 rows)
- **Review data**: Customer satisfaction ratings (98,410 rows)
- **Geographic data**: Brazilian location mapping (19,177 rows)

Perfect for building marketing dashboards with customer segmentation, sales trends, and geographic analysis!

## 🔧 Data Sources

This dashboard works with the following BigQuery tables:
- `dim_customer` - Customer demographics and location
- `dim_orders` - Order information and status
- `fact_order_items` - Order line items and pricing
- `dim_order_reviews` - Customer reviews and ratings
- `dim_geolocation` - Geographic coordinates and location data

## 🛠️ Customization

To adapt this dashboard for your data:
1. Edit `config/bigquery_config.json` with your project details
2. Update SQL queries to match your table schema
3. Customize visualizations and metrics as needed

## � Prerequisites

- Google Cloud account with BigQuery access
- Python 3.8+ with virtual environment
- BigQuery dataset with business data
- Polars (automatically installed via requirements.txt)

## 📞 Support

If you encounter issues:
1. Ensure virtual environment is activated:
   - Linux/Mac: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate.bat`
2. Verify all dependencies: `pip install -r requirements.txt`
3. Check Google Cloud authentication: `gcloud auth application-default login`
4. Test individual imports: `python -c "import polars as pl; print('Polars ready!')"`

---

**🎉 Your Polars-powered analytics dashboard is ready to use!**
