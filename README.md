# 💰 Expense Analytics

![Expense Tracker](https://img.shields.io/badge/Expense-Tracker-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28.1-red)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A comprehensive, user-friendly expense tracking system built with FastAPI backend and Streamlit frontend, designed specifically for Indian users with INR currency support.

# ✨ See It Live!
My project, **[Expense Analytics]**, is live and ready to explore.

            **👉 [View My Live Project](https://expense-tracker-analytics.streamlit.app/)**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/expense-tracker-pro.git
cd expense-tracker-pro
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the backend server**
```bash
python backend.py
```
Backend will be available at `http://localhost:8000`

4. **Run the frontend (in a new terminal)**
```bash
streamlit run frontend.py
```
Frontend will be available at `http://localhost:8501`

## ✨ Features

### 📊 Dashboard & Analytics
- **Real-time Financial Dashboard** with key metrics
- **Interactive Charts** for spending patterns
- **Category-wise Breakdown** with pie charts
- **Monthly Trend Analysis** with line graphs
- **Weekly Spending Comparison**
- **Daily Pattern Analysis**

### 💳 Expense Management
- **➕ Add Expenses** with rich metadata (category, priority, tags, notes)
- **📋 Smart Expense Listing** with advanced filtering
- **🔍 Powerful Search** across descriptions, categories, and tags
- **✏️ Edit & Delete** expenses seamlessly
- **🏷️ Tagging System** for better organization

### 🎯 Budget Management
- **💰 Custom Budget Limits** per category
- **⚠️ Smart Budget Alerts** (Critical, Warning, Info levels)
- **📈 Budget vs Actual** comparison
- **🎯 Financial Goal Tracking**

### 🔐 User Management
- **📱 Phone-based Authentication**
- **🔒 Secure 6-digit PIN system**
- **🔄 Password Reset** with admin code
- **👥 Multi-user Support**

### 📤 Data Management
- **📄 JSON & CSV Export** capabilities
- **📊 Custom Report Generation**
- **🔧 Admin Database Access**
- **📝 Sample Data Initialization**

### 🎨 User Experience
- **💰 INR Currency Support** optimized for Indian users
- **📱 Responsive Design** works on all devices
- **🎨 Modern UI/UX** with intuitive navigation
- **⚡ Fast Performance** with efficient data handling

## 🛠 Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | Streamlit | 1.28.1 |
| **Backend** | FastAPI | 0.104.1 |
| **API Server** | Uvicorn | 0.24.0 |
| **Data Processing** | Pandas | 2.1.3 |
| **Visualization** | Plotly | 5.17.0 |
| **HTTP Client** | Requests | 2.31.0 |
| **Deployment** | Render | Free Tier |

## 📁 Project Structure

```
expense-tracker-pro/
├── 📄 backend.py              # FastAPI backend server
├── 📄 frontend.py             # Streamlit frontend application
├── 📄 render.yaml             # Render deployment configuration
├── 📄 requirements.txt        # Python dependencies
├── 📄 expenses_data.json      # Expenses database (auto-generated)
├── 📄 users_data.json         # Users database (auto-generated)
├── 📄 budgets_data.json       # Budgets database (auto-generated)
└── 📄 README.md               # Project documentation
```

## 🔧 Architecture

```
┌─────────────────┐    REST API    ┌──────────────────┐
│   Streamlit     │ ◄────────────► │    FastAPI       │
│    Frontend     │                │    Backend       │
│  (Port: 8501)   │                │   (Port: 8000)   │
└─────────────────┘                └──────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌──────────────────┐
│   User Browser  │                │  JSON Database   │
│                 │                │  (Local Files)   │
└─────────────────┘                └──────────────────┘
```

## 📚 API Documentation

### Expense Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/expenses/` | Get all expenses with filtering |
| `POST` | `/expenses/` | Create new expense |
| `GET` | `/expenses/{id}` | Get specific expense |
| `PUT` | `/expenses/{id}` | Update expense |
| `DELETE` | `/expenses/{id}` | Delete expense |

### Analytics & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/overview` | Comprehensive analytics |
| `GET` | `/reports/export` | Export expenses (JSON/CSV) |
| `GET` | `/budgets/alerts` | Get budget alerts |

### User Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/register` | Register new user |
| `POST` | `/users/login` | User login |
| `POST` | `/users/forgot-password` | Password reset |

### Budget Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/budgets/{user_id}` | Get user budgets |
| `POST` | `/budgets/{user_id}` | Save user budgets |

## 🎯 Usage Examples

### Adding an Expense
```python
# Example expense payload
{
  "description": "Dinner at Restaurant",
  "amount": 850.0,
  "category": "Food & Dining",
  "date": "2024-01-15",
  "priority": "Medium",
  "tags": ["restaurant", "weekend"],
  "notes": "Family dinner celebration"
}
```

### Sample Analytics Response
```json
{
  "total_spent": 45250.0,
  "average_daily": 1508.33,
  "category_breakdown": {
    "Food & Dining": 12500.0,
    "Transportation": 5500.0,
    "Housing": 15000.0
  },
  "savings_rate": 23.5
}
```

## 🚀 Deployment

### Local Development
```bash
# Backend (Terminal 1)
python backend.py

# Frontend (Terminal 2)
streamlit run frontend.py
```

### Render Deployment
The project is configured for automatic deployment on Render:

1. **Backend Service**: FastAPI app on port 8000
2. **Frontend Service**: Streamlit app on port 8501
3. **Environment Variables**: Automatic configuration

### Environment Variables
```bash
BACKEND_URL=https://your-backend.onrender.com
PORT=8501  # For frontend
```

## 🤝 Contributing

We love contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
```bash
git checkout -b feature/amazing-feature
```
3. **Commit your changes**
```bash
git commit -m 'Add amazing feature'
```
4. **Push to the branch**
```bash
git push origin feature/amazing-feature
```
5. **Open a Pull Request**

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Support

If you find this project helpful, please give it a star! ⭐

## 🏆 Acknowledgements

- **FastAPI** - For the excellent async web framework
- **Streamlit** - For making data apps so accessible
- **Plotly** - For beautiful, interactive visualizations
- **Render** - For seamless deployment hosting
- **Pandas** - For powerful data manipulation

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0.0 | Jan 2024 | Enhanced analytics, budget alerts, multi-user support |
| v1.0.0 | Dec 2023 | Initial release with basic expense tracking |

## 🔗 Links

- **Documentation**: [GitHub Wiki](https://github.com/yourusername/expense-tracker-pro/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/expense-tracker-pro/issues)
- **Releases**: [GitHub Releases](https://github.com/yourusername/expense-tracker-pro/releases)

---

<div align="center">

### ⭐ Don't forget to star this repo if you found it useful! ⭐

**Built with ❤️ for the developer community**

</div>
