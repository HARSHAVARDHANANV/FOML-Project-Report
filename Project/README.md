# Customer Segmentation App

A full-stack web application for customer segmentation using machine learning. This application uses K-Means clustering to segment customers into 6 distinct groups and provides actionable business insights based on customer behavior patterns.

## Features

- **K-Means Clustering**: Automatically segments customers into 6 clusters based on multiple behavioral features
- **Interactive Dashboard**: Real-time visualization of customer segments
- **Scatter Plot Visualization**: View customer distribution by Income vs Spending Score with color-coded clusters
- **Detailed Segmentation**: 11+ customer segment types including:
  - VIP Customer
  - Churn Risk Customer
  - Dormant High Potential
  - Impulsive Buyer
  - Loyal Budget Shopper
  - Value Maximizer
  - And more...
- **Actionable Insights**: Get business recommendations for each customer segment
- **REST API**: Clean, well-documented API endpoints for programmatic access

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **ML Library**: Scikit-learn (K-Means clustering)
- **Data Processing**: Pandas, NumPy
- **Validation**: Pydantic

### Frontend
- **HTML/CSS/JavaScript**: Vanilla implementation (no build process required)
- **Visualization**: Chart.js
- **Styling**: Responsive CSS

### Data
- **Dataset**: `Customers_dataset.csv` (1000+ customer records)
- **Features**: CustomerID, Gender, Age, Income, SpendingScore, Frequency, Recency, Monetary

## Project Structure

```
customer-segmentation-app/
├── README.md                          # This file
├── Customers_dataset.csv              # Customer data for clustering
├── backend/
│   ├── main.py                        # FastAPI application & main entry point
│   ├── model.py                       # K-Means model and segmentation logic
│   └── requirements.txt               # Python package dependencies
└── frontend/
    ├── index.html                     # Main dashboard UI
    ├── script.js                      # Frontend logic & API integration
    └── style.css                      # Responsive styling
```

## Quick Start

### Prerequisites
- Python 3.8 or higher
- A modern web browser (Chrome, Firefox, Safari, Edge)

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
```

The backend API will be available at `http://localhost:8000`

### 2. Frontend Access

**Option A: Open directly in browser**
```
Open frontend/index.html in your web browser
```

**Option B: Serve with Python HTTP server**
```bash
# From the frontend directory
python -m http.server 8001

# Then open http://localhost:8001 in your browser
```

## API Endpoints

### Health Check
```
GET /health
```
Returns API health status.

### Segment a Customer
```
POST /segment
```
Segments a single customer based on their metrics.

**Request Body:**
```json
{
  "income": 50000,
  "spending_score": 75,
  "frequency": 12,
  "recency": 30,
  "monetary": 5000
}
```

**Response:**
```json
{
  "cluster": 2,
  "segment_name": "VIP Customer",
  "behavioral_pattern": "High-value, frequent purchaser with excellent lifetime value",
  "insight": "Focus on loyalty programs and personalized premium experiences"
}
```

### Get All Customer Data
```
GET /data
```
Returns all customers with their cluster assignments for visualization.

## How It Works

1. **Data Loading**: The application loads customer data from `Customers_dataset.csv`
2. **Feature Engineering**: Derives engineered features from raw customer metrics:
   - Value Score: Income × Spending Score
   - Engagement: Frequency × Monetary
   - Efficiency: Spending Score / Age
   - Loyalty: 1 / Recency
3. **K-Means Clustering**: Groups customers into 6 clusters based on these features
4. **Segmentation Mapping**: Each cluster is mapped to a business-friendly segment name with insights
5. **Visualization**: The frontend displays clusters as an interactive scatter plot

## Usage

1. Start the backend server (see Backend Setup above)
2. Open the frontend in your browser
3. Choose either:
   - **View All Segments**: See the scatter plot showing all customer clusters
   - **Segment a Customer**: Enter customer metrics in the form to get their segment classification and insights

## Development

### Backend Structure
- `main.py`: FastAPI application with CORS middleware and API endpoints
- `model.py`: Contains the K-Means model initialization, training, and customer segmentation logic

### Frontend Structure
- `index.html`: Dashboard layout with form input and chart container
- `script.js`: API communication, chart initialization, and event handling
- `style.css`: Responsive design with cluster color coding

### Running in Development Mode
```bash
# Backend with auto-reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend with hot-reload
cd frontend
python -m http.server 8001
```

## Verification

### Test Backend Connectivity
```bash
# Health check
curl http://localhost:8000/health

# Get all customer data
curl http://localhost:8000/data

# Segment a customer
curl -X POST http://localhost:8000/segment \
  -H "Content-Type: application/json" \
  -d '{"income": 50000, "spending_score": 75, "frequency": 12, "recency": 30, "monetary": 5000}'
```

### Test in Browser
1. Open `http://localhost:8001` (or direct file in browser)
2. You should see the customer segmentation dashboard
3. Try submitting customer data in the form
4. Verify the scatter plot displays and updates

## Notes

- **No Configuration Files Required**: The application works out of the box without `.env` files
- **No Build Process**: Frontend is static HTML/CSS/JS - no npm or compilation needed
- **CORS Enabled**: Frontend and backend can run on different ports/servers
- **Dataset Location**: Automatically searched in multiple locations relative to the backend

## License

This project is provided as-is for customer segmentation and analysis purposes.

```
customer-segmentation-app
├─ .claude
│  └─ CLAUDE.local.md
├─ backend
│  ├─ .env
│  ├─ .env.example
│  ├─ config.py
│  ├─ Customers_dataset.csv
│  ├─ main.py
│  ├─ model.py
│  ├─ requirements.txt
│  ├─ schemas.py
│  └─ __pycache__
│     ├─ config.cpython-313.pyc
│     ├─ model.cpython-313.pyc
│     └─ schemas.cpython-313.pyc
├─ Customers_dataset.csv
├─ frontend
│  ├─ index.html
│  ├─ script.js
│  └─ style.css
└─ README.md

```