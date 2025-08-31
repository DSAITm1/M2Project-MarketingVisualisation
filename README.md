# BigQuery Analytics Dashboard

A modern analytics dashboard using Streamlit to visualize BigQuery data with interactive charts and business intelligence.

## 🚀 Quick Start

1. **Setup Authentication**
   ```bash
   gcloud auth application-default login
   ```

2. **Launch Dashboard**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Start dashboard
   streamlit run Main.py
   ```

3. **Access Dashboard**: http://localhost:8501

## 📁 Project Structure

```
├── Main.py                      # Core dashboard application
├── utils/                       # Utility modules
│   ├── database.py              # Database operations
│   ├── visualizations.py        # Chart functions
│   ├── data_processing.py       # Business analytics
│   └── performance.py           # Performance monitoring
├── pages/                       # Analytics pages
│   ├── 1_👥_Customer_Analytics.py
│   ├── 2_🛒_Order_Analytics.py  
│   ├── 3_⭐_Review_Analytics.py
│   └── 4_🗺️_Geographic_Analytics.py
├── config/
│   └── bigquery_config.json    # Database configuration
└── requirements.txt             # Dependencies
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

## 🚀 Quick Start

1. **Setup Authentication**
   ```bash
   # Login to Google Cloud
   gcloud auth application-default login
   ```

2. **Install Dependencies**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install packages (already done)
   pip install -r requirements.txt
   ```

3. **Configure Project**
   - Edit `config/bigquery_config.json` with your project details

4. **Launch Dashboard**
   ```bash
   streamlit run Main.py
   ```

5. **Access Dashboard**
   - Open browser to `http://localhost:8501`
   - Navigate through different analytics pages
   - Use sidebar controls for data filtering

## � Advanced Analytics Features

### 📊 Executive Summary Dashboard
- **Real-time KPIs**: Revenue, customers, orders, ratings
- **Customer Segmentation**: Champions, Loyalists, At-Risk identification  
- **Geographic Intelligence**: State-level performance insights
- **Growth Opportunities**: Automated business recommendations

### 👥 Customer Intelligence  
- **RFM Segmentation**: Recency, Frequency, Monetary analysis
- **Cohort Analysis**: Customer retention tracking over time
- **Lifetime Value**: CLV calculations and predictions
- **Behavioral Insights**: Order patterns and preferences

### 🛒 Order Intelligence
- **Delivery Performance**: On-time delivery tracking and optimization
- **Order Value Analysis**: Revenue segmentation and trends
- **Status Monitoring**: Real-time order pipeline visibility
- **Performance Metrics**: Automated variance analysis

### ⭐ Review Intelligence
- **Sentiment Analysis**: Rating trends and category performance
- **Time-based Insights**: Monthly review patterns
- **Product Performance**: Category-level satisfaction metrics
- **Quality Monitoring**: Review response time analysis

## 📊 Dashboard Features

### � Main Dashboard (`Main.py`) - **🆕 Optimized**
- **Executive Summary**: High-level KPIs for leadership
- **Customer Deep Dive**: Advanced customer analytics
- **Order Intelligence**: Delivery and performance metrics  
- **Review Insights**: Satisfaction and sentiment analysis
- **🛠️ Debug Mode**: Performance monitoring (optional)
- **🔄 Data Management**: Smart caching with refresh controls

### 👥 Customer Analytics - **🆕 Enhanced**
- Advanced customer segmentation with business rules
- Customer lifetime value analysis and predictions
- Geographic performance with state-level insights  
- Cohort retention analysis for churn prevention

### 🛒 Order Analytics
- Order trends and seasonality
- Order status and fulfillment analysis
- Delivery performance metrics
- Revenue and order value insights

### ⭐ Review Analytics
- Customer satisfaction trends
- Review score analysis
- Comment sentiment insights
- Geographic satisfaction patterns

### 🗺️ Geographic Analytics
- Interactive Brazil map visualization
- State and city performance analysis
- Regional market insights
- Location-based business metrics

## 📊 Available Data (Olist E-commerce)
- **Customer data**: Demographics and location (99,441 rows)
- **Order data**: Purchase history and status (99,441 rows)
- **Review data**: Customer satisfaction ratings (98,410 rows)
- **Geographic data**: Brazilian location mapping (19,177 rows)

Perfect for building marketing dashboards with customer segmentation, sales trends, and geographic analysis!

## Data Sources

This dashboard works with the following BigQuery tables:
- `dim_customer` - Customer demographics and location
- `dim_orders` - Order information and status
- `fact_order_items` - Order line items and pricing
- `dim_order_reviews` - Customer reviews and ratings
- `dim_geolocation` - Geographic coordinates and location data

## Customization

To adapt this dashboard for your data:
1. Edit `config/bigquery_config.json` with your project details
2. Update SQL queries to match your table schema
3. Customize visualizations and metrics as needed

## 📊 Data Sources

- `dim_customer` - Customer demographics and location
- `dim_orders` - Order information and status  
- `fact_order_items` - Order line items and pricing
- `dim_order_reviews` - Customer reviews and ratings
- `dim_geolocation` - Geographic coordinates

## Prerequisites

- Google Cloud account with BigQuery access
- Python 3.8+ with virtual environment
- BigQuery dataset with business data
