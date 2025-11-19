from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
from enum import Enum
from supabase import create_client, Client

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

# Supabase configuration
SUPABASE_URL = "https://tinuhgygmhlnyugbinsm.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpbnVoZ3lnbWhsbnl1Z2JpbnNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1NzEzMjksImV4cCI6MjA3OTE0NzMyOX0.4y9pP8Auompl-7_vWjI3RrI2Opv8M7cduUyn1WiryVo"  # Replace with your Supabase anon key

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

class BudgetAlert(BaseModel):
    category: str
    spent: float
    budget: float
    percentage: float
    alert_level: str

def get_expenses():
    """Get all expenses from Supabase"""
    try:
        response = supabase.table("expenses").select("*").execute()
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

@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API is running",
        "version": "2.0.0",
        "database": "Supabase (Cloud)",
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
                top_expenses=[]
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
        
        return AnalyticsResponse(
            total_spent=total_spent,
            average_daily=average_daily,
            category_breakdown=category_breakdown,
            monthly_trend=monthly_trend,
            weekly_spending=weekly_data,
            priority_distribution=priority_distribution,
            top_expenses=top_expenses
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
        
        # Default budget limits (in a real app, these would be user-defined)
        default_budgets = {
            "Food & Dining": 500,
            "Transportation": 300,
            "Entertainment": 200,
            "Utilities": 400,
            "Shopping": 300,
            "Healthcare": 150,
            "Travel": 1000,
            "Education": 200,
            "Housing": 1200,
            "Other": 300
        }
        
        alerts = []
        for category, spent in monthly_expenses.items():
            budget = default_budgets.get(category, 500)
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
            # Simple CSV format
            csv_lines = ["Date,Category,Description,Amount,Priority"]
            for exp in expenses:
                csv_lines.append(f'{exp["date"]},{exp["category"]},"{exp["description"]}",{exp["amount"]},{exp["priority"]}')
            return {"csv": "\n".join(csv_lines)}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
