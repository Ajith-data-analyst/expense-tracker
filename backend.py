from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import re
import io
import speech_recognition as sr

app = FastAPI(
    title="Enhanced Expense Tracker API with Voice Assistant",
    version="3.1.0",
    description="A comprehensive expense tracking system with advanced analytics and voice control with audio intake"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage files
DATA_FILE = "expenses_data.json"
USERS_FILE = "users_data.json"
BUDGETS_FILE = "budgets_data.json"

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

class PasswordResetRequest(BaseModel):
    phone_number: str
    new_password: str
    admin_code: str

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

class VoiceCommand(BaseModel):
    command: str
    user_id: str = "default"

class VoiceResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    action: str

def load_data(filename):
    """Load data from JSON file with enhanced error handling"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {filename}: {e}")
        try:
            if os.path.exists(filename):
                backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(filename, backup_name)
                print(f"Created backup: {backup_name}")
        except Exception as backup_error:
            print(f"Backup creation failed: {backup_error}")
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def save_data(filename, data):
    """Save data to JSON file with enhanced error handling"""
    try:
        if os.path.exists(filename):
            backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(filename, 'r') as source, open(backup_name, 'w') as backup:
                backup.write(source.read())
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def validate_expense_data(expense_data):
    """Validate expense data before saving"""
    try:
        if not expense_data.get('description') or not expense_data.get('description').strip():
            return False, "Description is required"
        if expense_data.get('amount') is None or float(expense_data.get('amount', 0)) <= 0:
            return False, "Amount must be positive"
        if not expense_data.get('category') or not expense_data.get('category').strip():
            return False, "Category is required"
        if not expense_data.get('date'):
            return False, "Date is required"
        try:
            datetime.fromisoformat(expense_data['date'].replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid date format"
        try:
            float(expense_data['amount'])
        except (ValueError, TypeError):
            return False, "Amount must be a valid number"
        return True, "Valid"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_expenses(user_id="default"):
    """Get all expenses for a user with enhanced error handling"""
    try:
        data = load_data(DATA_FILE)
        user_expenses = data.get(user_id, [])
        valid_expenses = []
        for expense in user_expenses:
            is_valid, _ = validate_expense_data(expense)
            if is_valid:
                valid_expenses.append(expense)
        if len(valid_expenses) != len(user_expenses):
            data[user_id] = valid_expenses
            save_data(DATA_FILE, data)
            print(f"Cleaned {len(user_expenses) - len(valid_expenses)} invalid expenses for user {user_id}")
        return valid_expenses
    except Exception as e:
        print(f"Error getting expenses for user {user_id}: {e}")
        return []

def save_user_expenses(user_id, expenses):
    """Save expenses for a user with validation"""
    try:
        validated_expenses = []
        for expense in expenses:
            is_valid, message = validate_expense_data(expense)
            if is_valid:
                validated_expenses.append(expense)
            else:
                print(f"Skipping invalid expense for user {user_id}: {message}")
        data = load_data(DATA_FILE)
        data[user_id] = validated_expenses
        return save_data(DATA_FILE, data)
    except Exception as e:
        print(f"Error saving expenses for user {user_id}: {e}")
        return False

def get_users():
    """Get all users with enhanced error handling"""
    try:
        users = load_data(USERS_FILE)
        valid_users = {}
        for user_id, user_data in users.items():
            if isinstance(user_data, dict) and user_data.get('phone_number') and user_data.get('password'):
                valid_users[user_id] = user_data
        return valid_users
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_user(user_data):
    """Save user data with validation"""
    try:
        if not isinstance(user_data, dict) or not user_data.get('phone_number') or not user_data.get('password'):
            print("Invalid user data structure")
            return False
        users = get_users()
        users[user_data["id"]] = user_data
        return save_data(USERS_FILE, users)
    except Exception as e:
        print(f"Error saving user: {e}")
        return False

def load_budgets():
    """Load budgets from JSON file with enhanced error handling"""
    try:
        budgets = load_data(BUDGETS_FILE)
        valid_budgets = {}
        for user_id, user_budgets in budgets.items():
            if isinstance(user_budgets, dict):
                valid_budgets[user_id] = {}
                for category, amount in user_budgets.items():
                    try:
                        valid_budgets[user_id][category] = float(amount)
                    except (ValueError, TypeError):
                        print(f"Invalid budget amount for {user_id}.{category}: {amount}")
        return valid_budgets
    except Exception as e:
        print(f"Error loading budgets: {e}")
        return {}

def save_budgets(data):
    """Save budgets to JSON file with validation"""
    try:
        if not isinstance(data, dict):
            print("Invalid budgets data structure")
            return False
        for user_id, user_budgets in data.items():
            if not isinstance(user_budgets, dict):
                print(f"Invalid user budgets structure for {user_id}")
                return False
            for category, amount in user_budgets.items():
                try:
                    float(amount)
                except (ValueError, TypeError):
                    print(f"Invalid budget amount for {user_id}.{category}: {amount}")
                    return False
        return save_data(BUDGETS_FILE, data)
    except Exception as e:
        print(f"Error saving budgets: {e}")
        return False

def initialize_sample_data(user_id="default"):
    """Initialize sample data for Chennai computer science student with enhanced error handling"""
    try:
        existing_expenses = get_expenses(user_id)
        if len(existing_expenses) > 5:
            print(f"Already have {len(existing_expenses)} expenses, skipping sample data")
            return True
        print("Initializing sample data...")
        sample_expenses = generate_sample_data()
        all_expenses = existing_expenses + sample_expenses
        success = save_user_expenses(user_id, all_expenses)
        if success:
            print(f"✅ Sample data initialized successfully with {len(sample_expenses)} expenses")
        else:
            print("❌ Failed to save sample data")
        return success
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")
        return False

def generate_sample_data():
    """Generate 3 months of sample expense data for Chennai CS student"""
    sample_data = []
    base_date = datetime.now() - timedelta(days=90)

    monthly_expenses = [
        {"desc": "Hostel Rent", "amount": 8000, "category": "Housing", "tags": ["hostel", "rent"]},
        {"desc": "College Fees", "amount": 5000, "category": "Education", "tags": ["college", "fees"]},
        {"desc": "Internet Bill", "amount": 700, "category": "Utilities", "tags": ["wifi", "internet"]},
        {"desc": "Mobile Recharge", "amount": 299, "category": "Utilities", "tags": ["mobile", "recharge"]},
    ]

    food_items = [
        {"desc": "Mess Lunch", "amount": 80, "tags": ["mess", "lunch"]},
        {"desc": "Mess Dinner", "amount": 80, "tags": ["mess", "dinner"]},
        {"desc": "Breakfast", "amount": 50, "tags": ["breakfast", "canteen"]},
        {"desc": "Tea/Snacks", "amount": 30, "tags": ["tea", "snacks"]},
        {"desc": "Restaurant", "amount": 300, "tags": ["restaurant", "treat"]},
    ]

    transport_items = [
        {"desc": "Bus Pass", "amount": 500, "tags": ["bus", "monthly"]},
        {"desc": "Auto", "amount": 100, "tags": ["auto", "local"]},
        {"desc": "Metro", "amount": 60, "tags": ["metro"]},
    ]

    entertainment_items = [
        {"desc": "Movie Ticket", "amount": 200, "tags": ["movie", "entertainment"]},
        {"desc": "Coffee Shop", "amount": 150, "tags": ["coffee", "friends"]},
        {"desc": "Shopping", "amount": 500, "tags": ["clothes", "shopping"]},
    ]

    education_items = [
        {"desc": "Books", "amount": 800, "tags": ["books", "study"]},
        {"desc": "Online Course", "amount": 1200, "tags": ["course", "online"]},
        {"desc": "Stationery", "amount": 200, "tags": ["stationery", "college"]},
    ]

    current_date = base_date
    expense_count = 0

    while current_date <= datetime.now():
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

        if random.random() > 0.1:
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

        if current_date.weekday() == 6 and random.random() > 0.3:
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
        "message": "Enhanced Expense Tracker API with Voice Assistant (Audio Intake)",
        "version": "3.1.0",
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "status": "healthy",
        "voice_assistant": "Enabled with Audio Intake"
    }

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate, user_id: str = "default"):
    """Create a new expense with enhanced fields and validation"""
    try:
        expense_dict = expense.dict()
        is_valid, message = validate_expense_data(expense_dict)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        expenses = get_expenses(user_id)
        expense_data = expense_dict
        expense_data["id"] = str(uuid.uuid4())
        expense_data["created_at"] = datetime.now().isoformat()
        expense_data["updated_at"] = datetime.now().isoformat()
        expenses.append(expense_data)
        if save_user_expenses(user_id, expenses):
            return expense_data
        else:
            raise HTTPException(status_code=500, detail="Failed to save expense")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

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
    """Get expenses with advanced filtering and error handling"""
    try:
        expenses = get_expenses(user_id)
        filtered_expenses = expenses

        if search and search.strip():
            search_lower = search.lower().strip()
            filtered_expenses = [
                exp for exp in filtered_expenses
                if (search_lower in exp["description"].lower()
                    or search_lower in exp["category"].lower()
                    or any(search_lower in tag.lower() for tag in exp.get("tags", [])))
            ]

        if category and category != "All":
            filtered_expenses = [exp for exp in filtered_expenses if exp["category"] == category]
        if start_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] >= start_date]
        if end_date:
            filtered_expenses = [exp for exp in filtered_expenses if exp["date"] <= end_date]
        if min_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if float(exp["amount"]) >= min_amount]
        if max_amount is not None:
            filtered_expenses = [exp for exp in filtered_expenses if float(exp["amount"]) <= max_amount]
        if priority and priority != "All":
            filtered_expenses = [exp for exp in filtered_expenses if exp["priority"] == priority]
        if tags and tags.strip():
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
            filtered_expenses = [
                exp for exp in filtered_expenses
                if any(tag in [t.lower() for t in exp.get("tags", [])] for tag in tag_list)
            ]

        filtered_expenses.sort(key=lambda x: x["date"], reverse=True)
        return filtered_expenses[skip:skip + limit]
    except Exception as e:
        print(f"Error reading expenses: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading expenses: {str(e)}")

@app.get("/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: str, user_id: str = "default"):
    """Get a specific expense by ID"""
    try:
        expenses = get_expenses(user_id)
        expense = next((exp for exp in expenses if exp["id"] == expense_id), None)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, expense_update: ExpenseUpdate, user_id: str = "default"):
    """Update an existing expense"""
    try:
        expenses = get_expenses(user_id)
        expense_index = next((i for i, exp in enumerate(expenses) if exp["id"] == expense_id), None)
        if expense_index is None:
            raise HTTPException(status_code=404, detail="Expense not found")

        expense = expenses[expense_index]
        update_data = expense_update.dict(exclude_unset=True)
        expense.update(update_data)
        expense["updated_at"] = datetime.now().isoformat()

        is_valid, message = validate_expense_data(expense)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        expenses[expense_index] = expense
        if save_user_expenses(user_id, expenses):
            return expense
        else:
            raise HTTPException(status_code=500, detail="Failed to update expense")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, user_id: str = "default"):
    """Delete an expense"""
    try:
        expenses = get_expenses(user_id)
        expenses = [exp for exp in expenses if exp["id"] != expense_id]
        if len(expenses) == len(get_expenses(user_id)):
            raise HTTPException(status_code=404, detail="Expense not found")
        if save_user_expenses(user_id, expenses):
            return {"message": "Expense deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete expense")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/analytics/")
def get_analytics(user_id: str = "default", start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get advanced analytics with enhanced error handling"""
    try:
        expenses = get_expenses(user_id)
        if start_date:
            expenses = [exp for exp in expenses if exp["date"] >= start_date]
        if end_date:
            expenses = [exp for exp in expenses if exp["date"] <= end_date]

        if not expenses:
            return {
                "total_spent": 0,
                "average_daily": 0,
                "category_breakdown": {},
                "monthly_trend": [],
                "weekly_spending": [],
                "priority_distribution": {},
                "top_expenses": [],
                "daily_pattern": {},
                "spending_velocity": {"current_week": 0, "previous_week": 0, "change_percentage": 0},
                "savings_rate": 0
            }

        total_spent = sum(float(exp["amount"]) for exp in expenses)
        days = len(set(exp["date"] for exp in expenses))
        average_daily = total_spent / days if days > 0 else 0

        category_breakdown = {}
        for exp in expenses:
            category = exp["category"]
            amount = float(exp["amount"])
            category_breakdown[category] = category_breakdown.get(category, 0) + amount

        monthly_trend = []
        monthly_data = {}
        for exp in expenses:
            month = exp["date"][:7]
            amount = float(exp["amount"])
            if month not in monthly_data:
                monthly_data[month] = {"month": month, "total": 0, "count": 0}
            monthly_data[month]["total"] += amount
            monthly_data[month]["count"] += 1
        monthly_trend = sorted(monthly_data.values(), key=lambda x: x["month"])

        weekly_data = []
        weekly_totals = {}
        for exp in expenses:
            week_start = (datetime.fromisoformat(exp["date"]) - timedelta(days=datetime.fromisoformat(exp["date"]).weekday())).date()
            week_key = week_start.isoformat()
            amount = float(exp["amount"])
            if week_key not in weekly_totals:
                weekly_totals[week_key] = {"week": week_key, "total": 0}
            weekly_totals[week_key]["total"] += amount
        weekly_data = sorted(weekly_totals.values(), key=lambda x: x["week"])

        priority_distribution = {}
        for exp in expenses:
            priority = exp.get("priority", "Medium")
            amount = float(exp["amount"])
            priority_distribution[priority] = priority_distribution.get(priority, 0) + amount

        try:
            top_expenses = sorted(expenses, key=lambda x: float(x["amount"]), reverse=True)[:10]
        except:
            top_expenses = []

        daily_pattern = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                day_name = date.strftime("%A")
                amount = float(exp["amount"])
                daily_pattern[day_name] = daily_pattern.get(day_name, 0) + amount
            except:
                continue

        try:
            today = datetime.now().date()
            last_7_days_start = today - timedelta(days=7)
            previous_7_days_start = last_7_days_start - timedelta(days=7)
            last_7_days_spent = 0
            previous_7_days_spent = 0
            for exp in expenses:
                try:
                    exp_date = datetime.fromisoformat(exp["date"]).date()
                    amount = float(exp["amount"])
                    if last_7_days_start <= exp_date <= today:
                        last_7_days_spent += amount
                    elif previous_7_days_start <= exp_date < last_7_days_start:
                        previous_7_days_spent += amount
                except:
                    continue
            spending_velocity = {
                "current_week": last_7_days_spent,
                "previous_week": previous_7_days_spent,
                "change_percentage": ((last_7_days_spent - previous_7_days_spent) / previous_7_days_spent * 100) if previous_7_days_spent > 0 else 0
            }
        except:
            spending_velocity = {"current_week": 0, "previous_week": 0, "change_percentage": 0}

        try:
            monthly_income = 15000
            current_month = datetime.now().strftime("%Y-%m")
            current_month_spent = 0
            for exp in expenses:
                if exp["date"].startswith(current_month):
                    try:
                        current_month_spent += float(exp["amount"])
                    except (ValueError, TypeError):
                        continue
            savings_rate = max(0, ((monthly_income - current_month_spent) / monthly_income * 100)) if monthly_income > 0 else 0
        except:
            savings_rate = 0

        return {
            "total_spent": total_spent,
            "average_daily": average_daily,
            "category_breakdown": category_breakdown,
            "monthly_trend": monthly_trend,
            "weekly_spending": weekly_data,
            "priority_distribution": priority_distribution,
            "top_expenses": top_expenses,
            "daily_pattern": daily_pattern,
            "spending_velocity": spending_velocity,
            "savings_rate": savings_rate
        }
    except Exception as e:
        print(f"Error in analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/budgets/alerts")
def get_budget_alerts(user_id: str = "default"):
    """Get budget alerts based on spending patterns with enhanced error handling"""
    try:
        expenses = get_expenses(user_id)
        current_month = datetime.now().strftime("%Y-%m")
        monthly_expenses = {}
        for exp in expenses:
            try:
                if exp["date"].startswith(current_month):
                    category = exp["category"]
                    amount = float(exp["amount"])
                    monthly_expenses[category] = monthly_expenses.get(category, 0) + amount
            except (ValueError, TypeError):
                continue

        user_budgets = load_budgets().get(user_id, {})
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

        budgets = user_budgets if user_budgets else default_budgets
        alerts = []
        for category, budget in budgets.items():
            spent = monthly_expenses.get(category, 0)
            percentage = (spent / budget * 100) if budget > 0 else 0
            if percentage > 0:
                if percentage >= 90:
                    alert_level = "Critical"
                elif percentage >= 75:
                    alert_level = "Warning"
                elif percentage >= 50:
                    alert_level = "Caution"
                else:
                    alert_level = "Normal"
                alerts.append({
                    "category": category,
                    "spent": spent,
                    "budget": budget,
                    "percentage": percentage,
                    "alert_level": alert_level
                })
        return alerts
    except Exception as e:
        print(f"Error getting budget alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== VOICE ASSISTANT ENDPOINTS ====================

def parse_voice_command(command: str) -> Dict[str, Any]:
    """Parse voice command and extract intent and parameters"""
    command_lower = command.lower().strip()
    
    # CRUD Operations
    if any(word in command_lower for word in ["add", "create", "new", "log"]):
        amount_match = re.search(r'(\d+(?:\.\d{2})?)', command_lower)
        amount = float(amount_match.group(1)) if amount_match else 0
        
        categories = ["food", "transport", "entertainment", "education", "housing", "utilities", "shopping", "travel", "healthcare"]
        category = None
        for cat in categories:
            if cat in command_lower:
                category = cat.title()
                break
        
        description = command_lower.replace("add", "").replace("create", "").replace("new", "").replace("expense", "").replace("log", "").strip()
        for cat in categories:
            description = description.replace(cat, "").strip()
        description = re.sub(r'\d+(?:\.\d{2})?', '', description).strip()
        
        return {
            "action": "add_expense",
            "amount": amount,
            "category": category or "Other",
            "description": description or "Expense",
            "intent": "create"
        }
    
    elif any(word in command_lower for word in ["delete", "remove", "clear"]):
        return {"action": "delete_expense", "intent": "delete"}
    
    elif any(word in command_lower for word in ["update", "edit", "modify", "change"]):
        return {"action": "update_expense", "intent": "update"}
    
    elif any(word in command_lower for word in ["show", "list", "get", "display", "view"]):
        if "budget" in command_lower:
            return {"action": "show_budgets", "intent": "read"}
        elif "analytics" in command_lower or "analysis" in command_lower:
            return {"action": "show_analytics", "intent": "read"}
        elif "alerts" in command_lower:
            return {"action": "show_alerts", "intent": "read"}
        else:
            return {"action": "show_expenses", "intent": "read"}
    
    elif any(word in command_lower for word in ["filter", "search", "find"]):
        category_match = None
        categories = ["food", "transport", "entertainment", "education", "housing", "utilities", "shopping", "travel"]
        for cat in categories:
            if cat in command_lower:
                category_match = cat.title()
                break
        return {"action": "filter_expenses", "category": category_match, "intent": "read"}
    
    elif any(word in command_lower for word in ["total", "sum", "spent", "analytics", "summary", "report"]):
        return {"action": "show_analytics", "intent": "read"}
    
    elif any(word in command_lower for word in ["navigate", "go to", "open", "show"]):
        if "home" in command_lower:
            return {"action": "navigate_home", "intent": "navigation"}
        elif "analytics" in command_lower:
            return {"action": "navigate_analytics", "intent": "navigation"}
        elif "budget" in command_lower:
            return {"action": "navigate_budgets", "intent": "navigation"}
        elif "expense" in command_lower:
            return {"action": "navigate_expenses", "intent": "navigation"}
        else:
            return {"action": "navigate_home", "intent": "navigation"}
    
    elif any(word in command_lower for word in ["help", "what can", "how to"]):
        return {"action": "show_help", "intent": "info"}
    
    else:
        return {"action": "unknown", "intent": "unknown"}

@app.post("/voice/process")
def process_voice_command(voice_cmd: VoiceCommand):
    """Process voice commands for expense management"""
    try:
        user_id = voice_cmd.user_id
        command = voice_cmd.command
        
        parsed = parse_voice_command(command)
        action = parsed.get("action")
        intent = parsed.get("intent")
        
        if action == "add_expense":
            amount = parsed.get("amount", 0)
            category = parsed.get("category", "Other")
            description = parsed.get("description", "Expense")
            
            if amount <= 0:
                return VoiceResponse(
                    status="error",
                    message="Please specify a valid amount for the expense",
                    action="add_expense"
                )
            
            new_expense = ExpenseCreate(
                description=description,
                amount=amount,
                category=category,
                date=datetime.now().date().isoformat(),
                priority="Medium",
                tags=[],
                notes="Added via voice"
            )
            
            expenses = get_expenses(user_id)
            expense_dict = new_expense.dict()
            expense_dict["id"] = str(uuid.uuid4())
            expense_dict["created_at"] = datetime.now().isoformat()
            expense_dict["updated_at"] = datetime.now().isoformat()
            expenses.append(expense_dict)
            
            if save_user_expenses(user_id, expenses):
                return VoiceResponse(
                    status="success",
                    message=f"✅ Added expense: {description} of ₹{amount} in {category}",
                    data={"expense": expense_dict},
                    action="add_expense"
                )
            else:
                return VoiceResponse(
                    status="error",
                    message="Failed to save expense",
                    action="add_expense"
                )
        
        elif action == "show_expenses":
            expenses = get_expenses(user_id)
            total = sum(float(exp["amount"]) for exp in expenses)
            count = len(expenses)
            latest = expenses[-1] if expenses else None
            
            return VoiceResponse(
                status="success",
                message=f"You have {count} expenses totaling ₹{total:.2f}",
                data={
                    "total_expenses": count,
                    "total_amount": total,
                    "latest_expense": latest
                },
                action="show_expenses"
            )
        
        elif action == "show_analytics":
            analytics = get_analytics(user_id)
            top_category = max(analytics["category_breakdown"].items(), key=lambda x: x[1])[0] if analytics["category_breakdown"] else "None"
            top_amount = analytics["category_breakdown"].get(top_category, 0)
            
            return VoiceResponse(
                status="success",
                message=f"Total spent: ₹{analytics['total_spent']:.2f}. Top category: {top_category} (₹{top_amount:.2f}). Average daily: ₹{analytics['average_daily']:.2f}",
                data=analytics,
                action="show_analytics"
            )
        
        elif action == "show_budgets":
            alerts = get_budget_alerts(user_id)
            critical_count = sum(1 for a in alerts if a["alert_level"] == "Critical")
            warning_count = sum(1 for a in alerts if a["alert_level"] == "Warning")
            
            message = f"Budget Status: {critical_count} critical, {warning_count} warning"
            return VoiceResponse(
                status="success",
                message=message,
                data={"alerts": alerts},
                action="show_budgets"
            )
        
        elif action == "show_alerts":
            alerts = get_budget_alerts(user_id)
            return VoiceResponse(
                status="success",
                message=f"Found {len(alerts)} budget alerts",
                data={"alerts": alerts},
                action="show_alerts"
            )
        
        elif action == "filter_expenses":
            category = parsed.get("category")
            expenses = get_expenses(user_id)
            if category:
                expenses = [exp for exp in expenses if exp["category"].lower() == category.lower()]
                total = sum(float(exp["amount"]) for exp in expenses)
                return VoiceResponse(
                    status="success",
                    message=f"Found {len(expenses)} expenses in {category} totaling ₹{total:.2f}",
                    data={"expenses": expenses, "category": category, "total": total},
                    action="filter_expenses"
                )
            return VoiceResponse(
                status="error",
                message="Please specify a category to filter",
                action="filter_expenses"
            )
        
        elif action in ["navigate_home", "navigate_analytics", "navigate_budgets", "navigate_expenses"]:
            page_map = {
                "navigate_home": "Home",
                "navigate_analytics": "📊 Analytics",
                "navigate_budgets": "💳 Budget Alerts",
                "navigate_expenses": "📝 Manage Expenses"
            }
            page = page_map.get(action, "Home")
            return VoiceResponse(
                status="success",
                message=f"Navigating to {page}",
                data={"page": page},
                action=action
            )
        
        elif action == "show_help":
            help_text = """Available voice commands:
- Add/Create expense: "Add 500 rupees for food"
- Show expenses: "Show my expenses"
- Analytics/Report: "Show my analytics"
- Show budgets: "Show budget status"
- Filter: "Show food expenses"
- Navigate: "Go to analytics"
"""
            return VoiceResponse(
                status="success",
                message=help_text,
                action="show_help"
            )
        
        else:
            return VoiceResponse(
                status="error",
                message=f"I didn't understand: '{command}'. Try saying 'help' for available commands",
                action="unknown"
            )
    
    except Exception as e:
        return VoiceResponse(
            status="error",
            message=f"Error processing voice command: {str(e)}",
            action="error"
        )

@app.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio file to text using SpeechRecognition"""
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Create recognizer
        recognizer = sr.Recognizer()
        
        # Convert bytes to AudioData
        audio_file = io.BytesIO(audio_data)
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            # Try to transcribe with Google Speech Recognition
            text = recognizer.recognize_google(audio)
            
            return {
                "status": "success",
                "transcribed_text": text,
                "confidence": "high"
            }
        except sr.UnknownValueError:
            return {
                "status": "error",
                "message": "Could not understand audio. Please speak clearly.",
                "transcribed_text": None
            }
        except sr.RequestError as e:
            return {
                "status": "error",
                "message": f"Speech recognition service error: {str(e)}",
                "transcribed_text": None
            }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio processing error: {str(e)}")

@app.get("/voice/commands")
def get_voice_commands():
    """Get list of available voice commands"""
    return {
        "commands": {
            "add": ["Add 500 rupees for food", "Create expense of 1000 for education"],
            "view": ["Show my expenses", "List all transactions", "Display expenses"],
            "analytics": ["Show my analytics", "Get spending report", "Analytics summary"],
            "budgets": ["Show budget alerts", "Budget status", "Check budgets"],
            "filter": ["Show food expenses", "Filter by entertainment", "Transportation spending"],
            "navigate": ["Go to analytics", "Open expenses", "Navigate to budgets"],
            "help": ["Help", "What can you do", "Available commands"]
        }
    }

# Initialize sample data on startup
initialize_sample_data()
