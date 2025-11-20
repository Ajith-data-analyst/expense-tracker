from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
from enum import Enum
from supabase import create_client, Client
import random

app = FastAPI(
    title="Enhanced Expense Tracker API",
    version="2.0.0",
    description="A comprehensive expense tracking system with advanced analytics"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration - UPDATE WITH YOUR CREDENTIALS
SUPABASE_URL = "https://your-project.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "your-anon-key"  # Replace with your Supabase anon key

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ExpenseCategory(str, Enum):
    FOOD = "Food & Dining"
    TRANSPORT = "Transportation"
    ENTERTAINMENT = "Entertainment"
    UTILITIES = "Utilities"
    SHOPPING = "Shopping"
    HEALTHCARE = "Healthcare"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    HOUSING = "Housing"
    OTHER = "Other"

class ExpensePriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class ExpenseBase(BaseModel):
    description: str
    amount: float
    category: ExpenseCategory
    date: str
    priority: ExpensePriority = ExpensePriority.MEDIUM
    tags: List[str] = []
    notes: Optional[str] = None

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: str
    created_at: str
    updated_at: str

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    date: Optional[str] = None
    priority: Optional[ExpensePriority] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_spent: float
    average_daily: float
    category_breakdown: Dict[str, float]
    monthly_trend: List[Dict[str, Any]]
    weekly_spending: List[Dict[str, Any]]
    priority_distribution: Dict[str, float]
    top_expenses: List[Dict[str, Any]]
    daily_pattern: Dict[str, float]
    spending_velocity: Dict[str, float]
    savings_rate: float

class BudgetAlert(BaseModel):
    category: str
    spent: float
    budget: float
    percentage: float
    alert_level: str

def get_expenses():
    """Get all expenses from Supabase"""
    try:
        response = supabase.table("expenses").select("*").order("date", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return []

def save_expense(expense_data):
    """Save expense to Supabase"""
    try:
        response = supabase.table("expenses").insert(expense_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to save expense")

def update_expense_db(expense_id, update_data):
    """Update expense in Supabase"""
    try:
        response = supabase.table("expenses").update(update_data).eq("id", expense_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to update expense")

def delete_expense_db(expense_id):
    """Delete expense from Supabase"""
    try:
        response = supabase.table("expenses").delete().eq("id", expense_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error deleting expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete expense")

def initialize_sample_data():
    """Initialize sample data for Chennai computer science student"""
    try:
        existing_expenses = get_expenses()
        if len(existing_expenses) > 10:  # If already has data, don't insert
            return
        
        sample_expenses = generate_sample_data()
        for expense in sample_expenses:
            expense["tags"] = ",".join(expense["tags"])
            save_expense(expense)
        print("Sample data initialized successfully")
    except Exception as e:
        print(f"Error initializing sample data: {e}")

def generate_sample_data():
    """Generate 3 months of sample expense data for Chennai CS student"""
    sample_data = []
    base_date = datetime.now() - timedelta(days=90)
    
    # Monthly fixed expenses
    monthly_expenses = [
        {"desc": "Hostel Rent", "amount": 8000, "category": "Housing", "tags": ["hostel", "rent"]},
        {"desc": "College Fees", "amount": 5000, "category": "Education", "tags": ["college", "fees"]},
        {"desc": "Internet Bill", "amount": 700, "category": "Utilities", "tags": ["wifi", "internet"]},
        {"desc": "Mobile Recharge", "amount": 299, "category": "Utilities", "tags": ["mobile", "recharge"]},
    ]
    
    # Food expenses (daily)
    food_items = [
        {"desc": "Mess Lunch", "amount": 80, "tags": ["mess", "lunch"]},
        {"desc": "Mess Dinner", "amount": 80, "tags": ["mess", "dinner"]},
        {"desc": "Breakfast", "amount": 50, "tags": ["breakfast", "canteen"]},
        {"desc": "Tea/Snacks", "amount": 30, "tags": ["tea", "snacks"]},
        {"desc": "Restaurant", "amount": 300, "tags": ["restaurant", "treat"]},
    ]
    
    # Transportation
    transport_items = [
        {"desc": "Bus Pass", "amount": 500, "tags": ["bus", "monthly"]},
        {"desc": "Auto", "amount": 100, "tags": ["auto", "local"]},
        {"desc": "Metro", "amount": 60, "tags": ["metro"]},
    ]
    
    # Entertainment
    entertainment_items = [
        {"desc": "Movie Ticket", "amount": 200, "tags": ["movie", "entertainment"]},
        {"desc": "Coffee Shop", "amount": 150, "tags": ["coffee", "friends"]},
        {"desc": "Shopping", "amount": 500, "tags": ["clothes", "shopping"]},
    ]
    
    # Education
    education_items = [
        {"desc": "Books", "amount": 800, "tags": ["books", "study"]},
        {"desc": "Online Course", "amount": 1200, "tags": ["course", "online"]},
        {"desc": "Stationery", "amount": 200, "tags": ["stationery", "college"]},
    ]
    
    current_date = base_date
    while current_date <= datetime.now():
        # Add monthly expenses on 1st of each month
        if current_date.day == 1:
            for expense in monthly_expenses:
                sample_data.append({
                    "id": str(uuid.uuid4()),
                    "description": expense["desc"],
                    "amount": expense["amount"],
                    "category": expense["category"],
                    "date": current_date.isoformat(),
                    "priority": "High",
                    "tags": expense["tags"],
                    "notes": "Monthly expense",
                    "created_at": current_date.isoformat(),
                    "updated_at": current_date.isoformat()
                })
        
        # Daily food expenses (skip some days)
        if random.random() > 0.1:  # 90% days have food expenses
            food_count = random.randint(2, 4)
            for _ in range(food_count):
                food = random.choice(food_items)
                sample_data.append({
                    "id": str(uuid.uuid4()),
                    "description": food["desc"],
                    "amount": food["amount"],
                    "category": "Food & Dining",
                    "date": current_date.isoformat(),
                    "priority": "Medium",
                    "tags": food["tags"],
                    "notes": "Daily food expense",
                    "created_at": current_date.isoformat(),
                    "updated_at": current_date.isoformat()
                })
        
        # Transportation (3-4 times per week)
        if random.random() > 0.4:
            transport = random.choice(transport_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": transport["desc"],
                "amount": transport["amount"],
                "category": "Transportation",
                "date": current_date.isoformat(),
                "priority": "Medium",
                "tags": transport["tags"],
                "notes": "Transportation expense",
                "created_at": current_date.isoformat(),
                "updated_at": current_date.isoformat()
            })
        
        # Entertainment (once per week)
        if current_date.weekday() == 6 and random.random() > 0.3:  # Sundays
            entertainment = random.choice(entertainment_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": entertainment["desc"],
                "amount": entertainment["amount"],
                "category": "Entertainment",
                "date": current_date.isoformat(),
                "priority": "Low",
                "tags": entertainment["tags"],
                "notes": "Weekend entertainment",
                "created_at": current_date.isoformat(),
                "updated_at": current_date.isoformat()
            })
        
        # Education expenses (occasionally)
        if random.random() > 0.8:
            education = random.choice(education_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": education["desc"],
                "amount": education["amount"],
                "category": "Education",
                "date": current_date.isoformat(),
                "priority": "High",
                "tags": education["tags"],
                "notes": "Educational expense",
                "created_at": current_date.isoformat(),
                "updated_at": current_date.isoformat()
            })
        
        current_date += timedelta(days=1)
    
    return sample_data

@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API is running",
        "version": "2.0.0",
        "database": "Supabase (Cloud)",
        "currency": "INR",
        "endpoints": [
            "/expenses/ - CRUD operations",
            "/analytics/ - Comprehensive analytics",
            "/budgets/ - Budget management",
            "/reports/ - Financial reports"
        ]
    }

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate):
    """Create a new expense with enhanced fields"""
    try:
        expense_data = expense.dict()
        expense_data["id"] = str(uuid.uuid4())
        expense_data["created_at"] = datetime.now().isoformat()
        expense_data["updated_at"] = datetime.now().isoformat()
        
        # Convert tags list to string for Supabase storage
        expense_data["tags"] = ",".join(expense_data["tags"])
        
        saved_expense = save_expense(expense_data)
        if saved_expense:
            # Convert tags back to list for response
            if isinstance(saved_expense["tags"], str):
                saved_expense["tags"] = saved_expense["tags"].split(",") if saved_expense["tags"] else []
            return saved_expense
        else:
            raise HTTPException(status_code=500, detail="Failed to create expense")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/", response_model=List[Expense])
def read_expenses(
    category: Optional[ExpenseCategory] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    priority: Optional[ExpensePriority] = None,
    tags: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000
):
    """Get expenses with advanced filtering"""
    try:
        expenses = get_expenses()
        
        # Convert tags from string to list for each expense
        for expense in expenses:
            if isinstance(expense.get("tags"), str):
                expense["tags"] = expense["tags"].split(",") if expense["tags"] else []
        
        filtered_expenses = expenses
        
        # Apply filters
        if category:
            filtered_expenses = [exp for exp in filtered_expenses if exp["category"] == category]
        
        if start_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] >= start_date]
        
        if end_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] <= end_date]
        
        if min_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if exp["amount"] >= min_amount]
        
        if max_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if exp["amount"] <= max_amount]
        
        if priority:
            filtered_expenses = [exp for exp in filtered_expenses if exp["priority"] == priority]
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            filtered_expenses = [
                exp for exp in filtered_expenses 
                if any(tag in [t.lower() for t in exp.get("tags", [])] for tag in tag_list)
            ]
        
        return filtered_expenses[skip:skip + limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: str):
    """Get a specific expense by ID"""
    try:
        expenses = get_expenses()
        for expense in expenses:
            if expense["id"] == expense_id:
                # Convert tags from string to list
                if isinstance(expense.get("tags"), str):
                    expense["tags"] = expense["tags"].split(",") if expense["tags"] else []
                return expense
        raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, expense_update: ExpenseUpdate):
    """Update an existing expense"""
    try:
        update_data = expense_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Convert tags list to string for Supabase storage if present
        if "tags" in update_data and isinstance(update_data["tags"], list):
            update_data["tags"] = ",".join(update_data["tags"])
        
        updated_expense = update_expense_db(expense_id, update_data)
        if updated_expense:
            # Convert tags back to list for response
            if isinstance(updated_expense["tags"], str):
                updated_expense["tags"] = updated_expense["tags"].split(",") if updated_expense["tags"] else []
            return updated_expense
        else:
            raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    """Delete an expense by ID"""
    try:
        deleted_expense = delete_expense_db(expense_id)
        if deleted_expense:
            # Convert tags back to list for response
            if isinstance(deleted_expense["tags"], str):
                deleted_expense["tags"] = deleted_expense["tags"].split(",") if deleted_expense["tags"] else []
            return {"message": "Expense deleted successfully", "deleted_expense": deleted_expense}
        else:
            raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/overview", response_model=AnalyticsResponse)
def get_analytics_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive analytics"""
    try:
        expenses = get_expenses()
        
        # Apply date filter
        if start_date:
            expenses = [exp for exp in expenses if exp["date"] >= start_date]
        if end_date:
            expenses = [exp for exp in expenses if exp["date"] <= end_date]
        
        if not expenses:
            return AnalyticsResponse(
                total_spent=0,
                average_daily=0,
                category_breakdown={},
                monthly_trend=[],
                weekly_spending=[],
                priority_distribution={},
                top_expenses=[],
                daily_pattern={},
                spending_velocity={},
                savings_rate=0
            )
        
        # Basic calculations
        total_spent = sum(exp["amount"] for exp in expenses)
        
        # Date range for average daily
        dates = [datetime.fromisoformat(exp["date"]) for exp in expenses]
        min_date = min(dates)
        max_date = max(dates)
        days = (max_date - min_date).days + 1
        average_daily = total_spent / days if days > 0 else total_spent
        
        # Category breakdown
        category_breakdown = {}
        for exp in expenses:
            category = exp["category"]
            category_breakdown[category] = category_breakdown.get(category, 0) + exp["amount"]
        
        # Monthly trend
        monthly_data = {}
        for exp in expenses:
            date = datetime.fromisoformat(exp["date"])
            month_key = date.strftime("%Y-%m")
            monthly_data[month_key] = monthly_data.get(month_key, 0) + exp["amount"]
        
        monthly_trend = [{"month": month, "amount": amount} for month, amount in monthly_data.items()]
        
        # Weekly spending (last 8 weeks)
        weekly_data = []
        end_date = max_date
        for i in range(8):
            week_start = end_date - timedelta(days=end_date.weekday() + 7*i)
            week_end = week_start + timedelta(days=6)
            week_amount = sum(
                exp["amount"] for exp in expenses
                if week_start <= datetime.fromisoformat(exp["date"]) <= week_end
            )
            weekly_data.append({
                "week": week_start.strftime("%Y-%m-%d"),
                "amount": week_amount
            })
        weekly_data.reverse()
        
        # Priority distribution
        priority_distribution = {}
        for exp in expenses:
            priority = exp["priority"]
            priority_distribution[priority] = priority_distribution.get(priority, 0) + exp["amount"]
        
        # Top expenses
        top_expenses = sorted(expenses, key=lambda x: x["amount"], reverse=True)[:10]
        
        # Daily pattern (spending by day of week)
        daily_pattern = {}
        for exp in expenses:
            date = datetime.fromisoformat(exp["date"])
            day_name = date.strftime("%A")
            daily_pattern[day_name] = daily_pattern.get(day_name, 0) + exp["amount"]
        
        # Spending velocity (last 7 days vs previous 7 days)
        today = datetime.now()
        last_7_days_start = today - timedelta(days=7)
        previous_7_days_start = last_7_days_start - timedelta(days=7)
        
        last_7_days_spent = sum(
            exp["amount"] for exp in expenses
            if last_7_days_start <= datetime.fromisoformat(exp["date"]) <= today
        )
        
        previous_7_days_spent = sum(
            exp["amount"] for exp in expenses
            if previous_7_days_start <= datetime.fromisoformat(exp["date"]) < last_7_days_start
        )
        
        spending_velocity = {
            "current_week": last_7_days_spent,
            "previous_week": previous_7_days_spent,
            "change_percentage": ((last_7_days_spent - previous_7_days_spent) / previous_7_days_spent * 100) if previous_7_days_spent > 0 else 0
        }
        
        # Savings rate (assuming monthly income of 15000 INR for student)
        monthly_income = 15000
        current_month = today.strftime("%Y-%m")
        current_month_spent = sum(
            exp["amount"] for exp in expenses
            if exp["date"].startswith(current_month)
        )
        savings_rate = ((monthly_income - current_month_spent) / monthly_income * 100) if monthly_income > 0 else 0
        
        return AnalyticsResponse(
            total_spent=total_spent,
            average_daily=average_daily,
            category_breakdown=category_breakdown,
            monthly_trend=monthly_trend,
            weekly_spending=weekly_data,
            priority_distribution=priority_distribution,
            top_expenses=top_expenses,
            daily_pattern=daily_pattern,
            spending_velocity=spending_velocity,
            savings_rate=savings_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budgets/alerts")
def get_budget_alerts():
    """Get budget alerts based on spending patterns"""
    try:
        expenses = get_expenses()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Simple budget logic - you can enhance this with user-defined budgets
        monthly_expenses = {}
        for exp in expenses:
            if exp["date"].startswith(current_month):
                category = exp["category"]
                monthly_expenses[category] = monthly_expenses.get(category, 0) + exp["amount"]
        
        # Default budget limits in INR
        default_budgets = {
            "Food & Dining": 6000,
            "Transportation": 2000,
            "Entertainment": 1500,
            "Utilities": 1500,
            "Shopping": 2000,
            "Healthcare": 1000,
            "Travel": 3000,
            "Education": 3000,
            "Housing": 8000,
            "Other": 2000
        }
        
        alerts = []
        for category, spent in monthly_expenses.items():
            budget = default_budgets.get(category, 5000)
            percentage = (spent / budget) * 100 if budget > 0 else 0
            
            if percentage >= 90:
                alert_level = "Critical"
            elif percentage >= 75:
                alert_level = "Warning"
            elif percentage >= 50:
                alert_level = "Info"
            else:
                continue
            
            alerts.append(BudgetAlert(
                category=category,
                spent=spent,
                budget=budget,
                percentage=percentage,
                alert_level=alert_level
            ))
        
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/export")
def export_expenses_report(
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export expenses in different formats"""
    try:
        expenses = get_expenses()
        
        # Apply date filter
        if start_date:
            expenses = [exp for exp in expenses if exp["date"] >= start_date]
        if end_date:
            expenses = [exp for exp in expenses if exp["date"] <= end_date]
        
        if format == "json":
            return expenses
        elif format == "csv":
            # Enhanced CSV format with all fields
            csv_lines = ["ID,Date,Category,Description,Amount,Priority,Tags,Notes"]
            for exp in expenses:
                tags_str = ";".join(exp.get("tags", [])) if isinstance(exp.get("tags"), list) else exp.get("tags", "")
                notes_str = exp.get("notes", "").replace('"', '""')
                description_str = exp.get("description", "").replace('"', '""')
                csv_lines.append(
                    f'{exp["id"]},{exp["date"]},{exp["category"]},'
                    f'"{description_str}",{exp["amount"]},{exp["priority"]},'
                    f'"{tags_str}","{notes_str}"'
                )
            return {"csv": "\n".join(csv_lines)}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sample-data/initialize")
def initialize_sample_data_endpoint():
    """Initialize sample data endpoint"""
    try:
        initialize_sample_data()
        return {"message": "Sample data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize sample data when backend starts
initialize_sample_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)