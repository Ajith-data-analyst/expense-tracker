from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import zipfile
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(
    title="Enhanced Expense Tracker API",
    version="2.1.0",
    description="A comprehensive expense tracking system with advanced analytics and password recovery"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Data storage files
DATA_FILE = "expenses_data.json"
USERS_FILE = "users_data.json"
BUDGETS_FILE = "budgets_data.json"
RESET_CODES_FILE = "reset_codes.json"

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

class UserCreate(BaseModel):
    phone_number: str
    password: str

class User(BaseModel):
    id: str
    phone_number: str
    created_at: str

class ForgotPasswordRequest(BaseModel):
    phone_number: str

class ResetPasswordRequest(BaseModel):
    phone_number: str
    reset_code: str
    new_password: str

class ExportPasswordRequest(BaseModel):
    password: str

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

def load_data(filename):
    """Load data from JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def save_data(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def get_expenses(user_id="default"):
    """Get all expenses for a user"""
    data = load_data(DATA_FILE)
    return data.get(user_id, [])

def save_user_expenses(user_id, expenses):
    """Save expenses for a user"""
    data = load_data(DATA_FILE)
    data[user_id] = expenses
    return save_data(DATA_FILE, data)

def get_users():
    """Get all users"""
    return load_data(USERS_FILE)

def save_user(user_data):
    """Save user data"""
    users = get_users()
    users[user_data["id"]] = user_data
    return save_data(USERS_FILE, users)

def load_budgets():
    """Load budgets from JSON file"""
    try:
        if os.path.exists(BUDGETS_FILE):
            with open(BUDGETS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {BUDGETS_FILE}: {e}")
        return {}

def save_budgets(data):
    """Save budgets to JSON file"""
    try:
        with open(BUDGETS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {BUDGETS_FILE}: {e}")
        return False

def load_reset_codes():
    """Load reset codes from JSON file"""
    try:
        if os.path.exists(RESET_CODES_FILE):
            with open(RESET_CODES_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {RESET_CODES_FILE}: {e}")
        return {}

def save_reset_codes(data):
    """Save reset codes to JSON file"""
    try:
        with open(RESET_CODES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {RESET_CODES_FILE}: {e}")
        return False

def generate_reset_code():
    """Generate a 6-digit reset code"""
    return str(random.randint(100000, 999999))

def send_reset_code_sms(phone_number, code):
    """Simulate sending reset code via SMS"""
    print(f"SMS sent to {phone_number}: Your password reset code is {code}")
    # In a real application, integrate with SMS service like Twilio
    return True

def initialize_sample_data(user_id="default"):
    """Initialize sample data for Chennai computer science student"""
    try:
        existing_expenses = get_expenses(user_id)
        if len(existing_expenses) > 5:  # If already has data, don't insert
            print(f"Already have {len(existing_expenses)} expenses, skipping sample data")
            return
        print("Initializing sample data...")
        sample_expenses = generate_sample_data()
        all_expenses = existing_expenses + sample_expenses
        save_user_expenses(user_id, all_expenses)
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
        "version": "2.1.0",
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "status": "healthy",
        "features": ["password_recovery", "data_export", "analytics"]
    }

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate, user_id: str = "default"):
    """Create a new expense with enhanced fields"""
    try:
        expenses = get_expenses(user_id)
        expense_data = expense.dict()
        expense_data["id"] = str(uuid.uuid4())
        expense_data["created_at"] = datetime.now().isoformat()
        expense_data["updated_at"] = datetime.now().isoformat()
        expenses.append(expense_data)
        if save_user_expenses(user_id, expenses):
            return expense_data
        else:
            raise HTTPException(status_code=500, detail="Failed to save expense")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/", response_model=List[Expense])
def read_expenses(
    user_id: str = "default",
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    priority: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000
):
    """Get expenses with advanced filtering"""
    try:
        expenses = get_expenses(user_id)
        filtered_expenses = expenses
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            filtered_expenses = [
                exp for exp in filtered_expenses
                if search_lower in exp["description"].lower()
                or search_lower in exp["category"].lower()
                or any(search_lower in tag.lower() for tag in exp.get("tags", []))
            ]
        
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
        
        # Sort by date descending (newest first)
        filtered_expenses.sort(key=lambda x: x["date"], reverse=True)
        
        # Apply pagination
        end_index = skip + limit
        return filtered_expenses[skip:end_index]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: str, user_id: str = "default"):
    """Get a specific expense by ID"""
    try:
        expenses = get_expenses(user_id)
        for expense in expenses:
            if expense["id"] == expense_id:
                return expense
        raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, expense_update: ExpenseUpdate, user_id: str = "default"):
    """Update an existing expense"""
    try:
        expenses = get_expenses(user_id)
        for expense in expenses:
            if expense["id"] == expense_id:
                update_data = expense_update.dict(exclude_unset=True)
                update_data["updated_at"] = datetime.now().isoformat()
                expense.update(update_data)
                if save_user_expenses(user_id, expenses):
                    return expense
                else:
                    raise HTTPException(status_code=500, detail="Failed to update expense")
        raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, user_id: str = "default"):
    """Delete an expense by ID"""
    try:
        expenses = get_expenses(user_id)
        for i, expense in enumerate(expenses):
            if expense["id"] == expense_id:
                deleted_expense = expenses.pop(i)
                if save_user_expenses(user_id, expenses):
                    return {"message": "Expense deleted successfully", "deleted_expense": deleted_expense}
                else:
                    raise HTTPException(status_code=500, detail="Failed to delete expense")
        raise HTTPException(status_code=404, detail="Expense not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/overview")
def get_analytics_overview(
    user_id: str = "default",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive analytics"""
    try:
        expenses = get_expenses(user_id)
        
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
        
        monthly_trend = [{"month": month, "amount": amount} for month, amount in sorted(monthly_data.items())]
        
        # Weekly spending
        weekly_data = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                week_key = date.strftime("%Y-W%W")
                weekly_data[week_key] = weekly_data.get(week_key, 0) + float(exp["amount"])
            except:
                continue
        
        sorted_weeks = sorted(weekly_data.items())[-8:]  # Last 8 weeks
        weekly_spending = [{"week": week, "amount": amount} for week, amount in sorted_weeks]
        
        # Priority distribution
        priority_distribution = {}
        for exp in expenses:
            priority = exp.get("priority", "Medium")
            priority_distribution[priority] = priority_distribution.get(priority, 0) + float(exp["amount"])
        
        # Top expenses
        sorted_expenses = sorted(expenses, key=lambda x: float(x["amount"]), reverse=True)
        top_expenses = sorted_expenses[:10]
        
        # Daily pattern
        daily_pattern = {}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                day = day_names[date.weekday()]
                daily_pattern[day] = daily_pattern.get(day, 0) + float(exp["amount"])
            except:
                continue
        
        # Spending velocity
        if len(weekly_spending) >= 2:
            current_week = weekly_spending[-1]["amount"]
            previous_week = weekly_spending[-2]["amount"]
            change = ((current_week - previous_week) / previous_week * 100) if previous_week > 0 else 0
            spending_velocity = {
                "current_week": current_week,
                "previous_week": previous_week,
                "change_percentage": change
            }
        else:
            spending_velocity = {"current_week": 0, "previous_week": 0, "change_percentage": 0}
        
        # Savings rate (assuming 20000 monthly income for student)
        monthly_income = 20000
        monthly_avg_spent = total_spent / max(len(monthly_data), 1)
        savings_rate = ((monthly_income - monthly_avg_spent) / monthly_income * 100) if monthly_income > 0 else 0
        
        return {
            "total_spent": total_spent,
            "average_daily": average_daily,
            "category_breakdown": category_breakdown,
            "monthly_trend": monthly_trend,
            "weekly_spending": weekly_spending,
            "priority_distribution": priority_distribution,
            "top_expenses": top_expenses,
            "daily_pattern": daily_pattern,
            "spending_velocity": spending_velocity,
            "savings_rate": max(0, savings_rate)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sample-data/initialize")
def init_sample_data(user_id: str = "default"):
    """Initialize sample data for user"""
    try:
        initialize_sample_data(user_id)
        return {"message": "Sample data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/register")
def register_user(user: UserCreate):
    """Register a new user"""
    try:
        users = get_users()
        
        # Check if phone number already exists
        for user_data in users.values():
            if user_data["phone_number"] == user.phone_number:
                raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "phone_number": user.phone_number,
            "password": user.password,
            "created_at": datetime.now().isoformat()
        }
        
        if save_user(user_data):
            return {"message": "User registered successfully", "user_id": user_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to register user")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/login")
def login_user(user: UserCreate):
    """Login user"""
    try:
        users = get_users()
        
        # Find user by phone number
        for user_id, user_data in users.items():
            if (user_data["phone_number"] == user.phone_number and
                user_data["password"] == user.password):
                return {"message": "Login successful", "user_id": user_id}
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get user by ID"""
    try:
        users = get_users()
        if user_id in users:
            user_data = users[user_id].copy()
            user_data.pop("password", None)  # Don't return password
            return user_data
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """Request password reset code"""
    try:
        users = get_users()
        
        # Find user by phone number
        user_found = None
        for user_id, user_data in users.items():
            if user_data["phone_number"] == request.phone_number:
                user_found = user_data
                break
        
        if not user_found:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate reset code
        reset_code = generate_reset_code()
        reset_codes = load_reset_codes()
        
        # Store reset code with expiration (10 minutes)
        reset_codes[request.phone_number] = {
            "code": reset_code,
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "user_id": user_found["id"]
        }
        
        save_reset_codes(reset_codes)
        
        # Send reset code (simulated)
        send_reset_code_sms(request.phone_number, reset_code)
        
        return {
            "message": "Reset code sent successfully",
            "code": reset_code,  # Remove this in production
            "expires_in": "10 minutes"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/reset-password")
def reset_password(request: ResetPasswordRequest):
    """Reset password using reset code"""
    try:
        reset_codes = load_reset_codes()
        
        if request.phone_number not in reset_codes:
            raise HTTPException(status_code=400, detail="Invalid reset code")
        
        reset_data = reset_codes[request.phone_number]
        
        # Check if code matches
        if reset_data["code"] != request.reset_code:
            raise HTTPException(status_code=400, detail="Invalid reset code")
        
        # Check if code expired
        expires_at = datetime.fromisoformat(reset_data["expires_at"])
        if datetime.now() > expires_at:
            del reset_codes[request.phone_number]
            save_reset_codes(reset_codes)
            raise HTTPException(status_code=400, detail="Reset code expired")
        
        # Update user password
        users = get_users()
        user_id = reset_data["user_id"]
        
        if user_id not in users:
            raise HTTPException(status_code=404, detail="User not found")
        
        users[user_id]["password"] = request.new_password
        save_data(USERS_FILE, users)
        
        # Remove used reset code
        del reset_codes[request.phone_number]
        save_reset_codes(reset_codes)
        
        return {"message": "Password reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/export-all-data")
def export_all_data(user_id: str, request: ExportPasswordRequest):
    """Export all user data as ZIP file"""
    try:
        # Verify password
        if request.password != "2139":
            raise HTTPException(status_code=401, detail="Invalid export password")
        
        # Get all user data
        expenses = get_expenses(user_id)
        budgets = load_budgets().get(user_id, {})
        users = get_users()
        user_data = users.get(user_id, {})
        
        # Remove password from user data
        if user_data:
            user_data = user_data.copy()
            user_data.pop("password", None)
        
        # Create temporary directory
        temp_dir = f"temp_export_{user_id}_{uuid.uuid4().hex}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save data to files
        with open(f"{temp_dir}/expenses.json", "w") as f:
            json.dump(expenses, f, indent=2)
        
        with open(f"{temp_dir}/budgets.json", "w") as f:
            json.dump(budgets, f, indent=2)
        
        with open(f"{temp_dir}/user_profile.json", "w") as f:
            json.dump(user_data, f, indent=2)
        
        # Create analytics summary
        analytics = get_analytics_overview(user_id)
        with open(f"{temp_dir}/analytics_summary.json", "w") as f:
            json.dump(analytics, f, indent=2)
        
        # Create ZIP file
        zip_filename = f"{temp_dir}_export.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in ["expenses.json", "budgets.json", "user_profile.json", "analytics_summary.json"]:
                zipf.write(f"{temp_dir}/{file}", file)
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        # Return ZIP file
        return FileResponse(
            path=zip_filename,
            filename=f"expense_tracker_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            media_type='application/zip'
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize sample data when backend starts
try:
    initialize_sample_data()
except Exception as e:
    print(f"Failed to initialize sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
