from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
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
SUPABASE_URL = "https://tinuhgygmhlnyugbinsm.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRpbnVoZ3lnbWhsbnl1Z2JpbnNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM1NzEzMjksImV4cCI6MjA3OTE0NzMyOX0.4y9pP8Auompl-7_vWjI3RrI2Opv8M7cduUyn1WiryVo"  # Replace with your Supabase anon key


# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Supabase client: {e}")
    supabase = None

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
    category: str
    date: str
    priority: str = "Medium"
    tags: List[str] = []
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class Expense(ExpenseBase):
    id: str
    created_at: str
    updated_at: str

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    date: Optional[str] = None
    priority: Optional[str] = None
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
        if not supabase:
            return []
        response = supabase.table("expenses").select("*").order("date", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return []

def save_expense(expense_data):
    """Save expense to Supabase"""
    try:
        if not supabase:
            raise Exception("Supabase client not initialized")
        response = supabase.table("expenses").insert(expense_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to save expense")

def update_expense_db(expense_id, update_data):
    """Update expense in Supabase"""
    try:
        if not supabase:
            raise Exception("Supabase client not initialized")
        response = supabase.table("expenses").update(update_data).eq("id", expense_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to update expense")

def delete_expense_db(expense_id):
    """Delete expense from Supabase"""
    try:
        if not supabase:
            raise Exception("Supabase client not initialized")
        response = supabase.table("expenses").delete().eq("id", expense_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error deleting expense: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete expense")

def initialize_sample_data():
    """Initialize sample data for Chennai computer science student"""
    try:
        if not supabase:
            print("Supabase not initialized, skipping sample data")
            return
            
        existing_expenses = get_expenses()
        if len(existing_expenses) > 5:  # If already has data, don't insert
            print(f"Already have {len(existing_expenses)} expenses, skipping sample data")
            return
        
        print("Initializing sample data...")
        sample_expenses = generate_sample_data()
        
        for expense in sample_expenses:
            # Convert tags list to string for storage
            if 'tags' in expense and isinstance(expense['tags'], list):
                expense['tags'] = ','.join(expense['tags'])
            save_expense(expense)
            
        print(f"✅ Sample data initialized successfully with {len(sample_expenses)} expenses")
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")

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
    expense_count = 0
    
    while current_date <= datetime.now():
        # Add monthly expenses on 1st of each month
        if current_date.day == 1:
            for expense in monthly_expenses:
                sample_data.append({
                    "id": str(uuid.uuid4()),
                    "description": expense["desc"],
                    "amount": float(expense["amount"]),
                    "category": expense["category"],
                    "date": current_date.date().isoformat(),
                    "priority": "High",
                    "tags": expense["tags"],
                    "notes": "Monthly expense",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
                expense_count += 1
        
        # Daily food expenses (skip some days)
        if random.random() > 0.1:  # 90% days have food expenses
            food_count = random.randint(2, 4)
            for _ in range(food_count):
                food = random.choice(food_items)
                sample_data.append({
                    "id": str(uuid.uuid4()),
                    "description": food["desc"],
                    "amount": float(food["amount"]),
                    "category": "Food & Dining",
                    "date": current_date.date().isoformat(),
                    "priority": "Medium",
                    "tags": food["tags"],
                    "notes": "Daily food expense",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
                expense_count += 1
        
        # Transportation (3-4 times per week)
        if random.random() > 0.4:
            transport = random.choice(transport_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": transport["desc"],
                "amount": float(transport["amount"]),
                "category": "Transportation",
                "date": current_date.date().isoformat(),
                "priority": "Medium",
                "tags": transport["tags"],
                "notes": "Transportation expense",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            expense_count += 1
        
        # Entertainment (once per week)
        if current_date.weekday() == 6 and random.random() > 0.3:  # Sundays
            entertainment = random.choice(entertainment_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": entertainment["desc"],
                "amount": float(entertainment["amount"]),
                "category": "Entertainment",
                "date": current_date.date().isoformat(),
                "priority": "Low",
                "tags": entertainment["tags"],
                "notes": "Weekend entertainment",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            expense_count += 1
        
        # Education expenses (occasionally)
        if random.random() > 0.8:
            education = random.choice(education_items)
            sample_data.append({
                "id": str(uuid.uuid4()),
                "description": education["desc"],
                "amount": float(education["amount"]),
                "category": "Education",
                "date": current_date.date().isoformat(),
                "priority": "High",
                "tags": education["tags"],
                "notes": "Educational expense",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            expense_count += 1
        
        current_date += timedelta(days=1)
    
    print(f"Generated {expense_count} sample expenses")
    return sample_data

@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API is running",
        "version": "2.0.0",
        "database": "Supabase (Cloud)",
        "currency": "INR",
        "status": "healthy"
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
        if 'tags' in expense_data and isinstance(expense_data['tags'], list):
            expense_data["tags"] = ",".join(expense_data["tags"])
        
        saved_expense = save_expense(expense_data)
        if saved_expense:
            # Convert tags back to list for response
            if isinstance(saved_expense.get("tags"), str):
                saved_expense["tags"] = saved_expense["tags"].split(",") if saved_expense["tags"] else []
            return saved_expense
        else:
            raise HTTPException(status_code=500, detail="Failed to create expense")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/", response_model=List[Expense])
def read_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    priority: Optional[str] = None,
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
        if category and category != "All":
            filtered_expenses = [exp for exp in filtered_expenses if exp["category"] == category]
        
        if start_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] >= start_date]
        
        if end_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] <= end_date]
        
        if min_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if exp["amount"] >= min_amount]
        
        if max_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if exp["amount"] <= max_amount]
        
        if priority and priority != "All":
            filtered_expenses = [exp for exp in filtered_expenses if exp["priority"] == priority]
        
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            filtered_expenses = [
                exp for exp in filtered_expenses 
                if any(tag in [t.lower() for t in exp.get("tags", [])] for tag in tag_list)
            ]
        
        # Apply pagination
        end_index = skip + limit
        return filtered_expenses[skip:end_index]
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
            if isinstance(updated_expense.get("tags"), str):
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
            if isinstance(deleted_expense.get("tags"), str):
                deleted_expense["tags"] = deleted_expense["tags"].split(",") if deleted_expense["tags"] else []
            return {"message": "Expense deleted successfully", "deleted_expense": deleted_expense}
        else:
            raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/overview")
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
            ).dict()
        
        # Basic calculations
        total_spent = sum(float(exp["amount"]) for exp in expenses)
        
        # Date range for average daily
        try:
            dates = [datetime.fromisoformat(exp["date"]) for exp in expenses]
            min_date = min(dates)
            max_date = max(dates)
            days = (max_date - min_date).days + 1
            average_daily = total_spent / days if days > 0 else total_spent
        except:
            average_daily = total_spent / 30  # Fallback
        
        # Category breakdown
        category_breakdown = {}
        for exp in expenses:
            category = exp["category"]
            category_breakdown[category] = category_breakdown.get(category, 0) + float(exp["amount"])
        
        # Monthly trend
        monthly_data = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key] = monthly_data.get(month_key, 0) + float(exp["amount"])
            except:
                continue
        
        monthly_trend = [{"month": month, "amount": amount} for month, amount in monthly_data.items()]
        
        # Weekly spending (last 8 weeks)
        weekly_data = []
        try:
            end_date_obj = max_date if 'max_date' in locals() else datetime.now()
            for i in range(8):
                week_start = end_date_obj - timedelta(days=end_date_obj.weekday() + 7*i)
                week_end = week_start + timedelta(days=6)
                week_amount = sum(
                    float(exp["amount"]) for exp in expenses
                    if week_start.date().isoformat() <= exp["date"] <= week_end.date().isoformat()
                )
                weekly_data.append({
                    "week": week_start.strftime("%Y-%m-%d"),
                    "amount": week_amount
                })
            weekly_data.reverse()
        except:
            weekly_data = []
        
        # Priority distribution
        priority_distribution = {}
        for exp in expenses:
            priority = exp.get("priority", "Medium")
            priority_distribution[priority] = priority_distribution.get(priority, 0) + float(exp["amount"])
        
        # Top expenses
        try:
            top_expenses = sorted(expenses, key=lambda x: float(x["amount"]), reverse=True)[:10]
        except:
            top_expenses = []
        
        # Daily pattern (spending by day of week)
        daily_pattern = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                day_name = date.strftime("%A")
                daily_pattern[day_name] = daily_pattern.get(day_name, 0) + float(exp["amount"])
            except:
                continue
        
        # Spending velocity (last 7 days vs previous 7 days)
        try:
            today = datetime.now().date()
            last_7_days_start = today - timedelta(days=7)
            previous_7_days_start = last_7_days_start - timedelta(days=7)
            
            last_7_days_spent = sum(
                float(exp["amount"]) for exp in expenses
                if last_7_days_start.isoformat() <= exp["date"] <= today.isoformat()
            )
            
            previous_7_days_spent = sum(
                float(exp["amount"]) for exp in expenses
                if previous_7_days_start.isoformat() <= exp["date"] < last_7_days_start.isoformat()
            )
            
            spending_velocity = {
                "current_week": last_7_days_spent,
                "previous_week": previous_7_days_spent,
                "change_percentage": ((last_7_days_spent - previous_7_days_spent) / previous_7_days_spent * 100) if previous_7_days_spent > 0 else 0
            }
        except:
            spending_velocity = {
                "current_week": 0,
                "previous_week": 0,
                "change_percentage": 0
            }
        
        # Savings rate (assuming monthly income of 15000 INR for student)
        try:
            monthly_income = 15000
            current_month = datetime.now().strftime("%Y-%m")
            current_month_spent = sum(
                float(exp["amount"]) for exp in expenses
                if exp["date"].startswith(current_month)
            )
            savings_rate = max(0, ((monthly_income - current_month_spent) / monthly_income * 100)) if monthly_income > 0 else 0
        except:
            savings_rate = 0
        
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
        ).dict()
    except Exception as e:
        print(f"Error in analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budgets/alerts")
def get_budget_alerts():
    """Get budget alerts based on spending patterns"""
    try:
        expenses = get_expenses()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Simple budget logic
        monthly_expenses = {}
        for exp in expenses:
            if exp["date"].startswith(current_month):
                category = exp["category"]
                monthly_expenses[category] = monthly_expenses.get(category, 0) + float(exp["amount"])
        
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
            
            alerts.append({
                "category": category,
                "spent": spent,
                "budget": budget,
                "percentage": percentage,
                "alert_level": alert_level
            })
        
        return alerts
    except Exception as e:
        print(f"Error in budget alerts: {e}")
        return []

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
                tags = exp.get("tags", [])
                if isinstance(tags, str):
                    tags_str = tags
                else:
                    tags_str = ";".join(tags) if tags else ""
                
                notes_str = str(exp.get("notes", "")).replace('"', '""')
                description_str = str(exp.get("description", "")).replace('"', '""')
                csv_lines.append(
                    f'{exp["id"]},{exp["date"]},{exp["category"]},'
                    f'"{description_str}",{exp["amount"]},{exp.get("priority", "Medium")},'
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
try:
    initialize_sample_data()
except Exception as e:
    print(f"Failed to initialize sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
