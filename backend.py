from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
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

def load_data(filename):
    """Load data from JSON file with enhanced error handling"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {filename}: {e}")
        # Try to recover by creating backup and returning empty dict
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
        # Create backup before saving
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
        # Check required fields
        if not expense_data.get('description') or not expense_data.get('description').strip():
            return False, "Description is required"
        
        if expense_data.get('amount') is None or float(expense_data.get('amount', 0)) <= 0:
            return False, "Amount must be positive"
        
        if not expense_data.get('category') or not expense_data.get('category').strip():
            return False, "Category is required"
        
        if not expense_data.get('date'):
            return False, "Date is required"
        
        # Validate date format
        try:
            datetime.fromisoformat(expense_data['date'].replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid date format"
        
        # Validate amount is numeric
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
        
        # Validate each expense and filter out invalid ones
        valid_expenses = []
        for expense in user_expenses:
            is_valid, _ = validate_expense_data(expense)
            if is_valid:
                valid_expenses.append(expense)
        
        # Save cleaned data if any were filtered out
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
        # Validate all expenses before saving
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
        # Validate user structure
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
        # Validate budget structure
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
        # Validate budget data structure
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
        if len(existing_expenses) > 5:  # If already has data, don't insert
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
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "status": "healthy"
    }

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate, user_id: str = "default"):
    """Create a new expense with enhanced fields and validation"""
    try:
        # Validate expense data
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
        
        # Apply search filter
        if search and search.strip():
            search_lower = search.lower().strip()
            filtered_expenses = [
                exp for exp in filtered_expenses 
                if (search_lower in exp["description"].lower() 
                or search_lower in exp["category"].lower()
                or any(search_lower in tag.lower() for tag in exp.get("tags", [])))
            ]
        
        # Apply filters
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
        
        # Sort by date descending (newest first)
        filtered_expenses.sort(key=lambda x: x["date"], reverse=True)
        
        # Apply pagination
        end_index = skip + limit
        return filtered_expenses[skip:end_index]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")

@app.get("/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: str, user_id: str = "default"):
    """Get a specific expense by ID with error handling"""
    try:
        expenses = get_expenses(user_id)
        for expense in expenses:
            if expense["id"] == expense_id:
                return expense
        raise HTTPException(status_code=404, detail="Expense not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expense: {str(e)}")

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: str, expense_update: ExpenseUpdate, user_id: str = "default"):
    """Update an existing expense with validation"""
    try:
        expenses = get_expenses(user_id)
        for expense in expenses:
            if expense["id"] == expense_id:
                update_data = expense_update.dict(exclude_unset=True)
                
                # Validate updated data
                test_expense = expense.copy()
                test_expense.update(update_data)
                is_valid, message = validate_expense_data(test_expense)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=message)
                
                update_data["updated_at"] = datetime.now().isoformat()
                expense.update(update_data)
                
                if save_user_expenses(user_id, expenses):
                    return expense
                else:
                    raise HTTPException(status_code=500, detail="Failed to update expense")
        
        raise HTTPException(status_code=404, detail="Expense not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating expense: {str(e)}")

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, user_id: str = "default"):
    """Delete an expense by ID with error handling"""
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting expense: {str(e)}")

@app.get("/analytics/overview")
def get_analytics_overview(
    user_id: str = "default",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive analytics with enhanced error handling"""
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
        
        # Basic calculations with proper error handling
        total_spent = 0
        for exp in expenses:
            try:
                total_spent += float(exp["amount"])
            except (ValueError, TypeError):
                continue
        
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
            try:
                category = exp["category"]
                amount = float(exp["amount"])
                category_breakdown[category] = category_breakdown.get(category, 0) + amount
            except (ValueError, TypeError):
                continue
        
        # Monthly trend
        monthly_data = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                month_key = date.strftime("%Y-%m")
                amount = float(exp["amount"])
                monthly_data[month_key] = monthly_data.get(month_key, 0) + amount
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
                week_amount = 0
                for exp in expenses:
                    try:
                        exp_date = datetime.fromisoformat(exp["date"]).date()
                        if week_start.date() <= exp_date <= week_end.date():
                            week_amount += float(exp["amount"])
                    except:
                        continue
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
            try:
                priority = exp.get("priority", "Medium")
                amount = float(exp["amount"])
                priority_distribution[priority] = priority_distribution.get(priority, 0) + amount
            except (ValueError, TypeError):
                continue
        
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
                amount = float(exp["amount"])
                daily_pattern[day_name] = daily_pattern.get(day_name, 0) + amount
            except:
                continue
        
        # Spending velocity (last 7 days vs previous 7 days)
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
            spending_velocity = {
                "current_week": 0,
                "previous_week": 0,
                "change_percentage": 0
            }
        
        # Savings rate (assuming monthly income of 15000 INR for student)
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
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/budgets/alerts")
def get_budget_alerts(user_id: str = "default"):
    """Get budget alerts based on spending patterns with enhanced error handling"""
    try:
        expenses = get_expenses(user_id)
        current_month = datetime.now().strftime("%Y-%m")
        
        # Calculate monthly expenses by category
        monthly_expenses = {}
        for exp in expenses:
            try:
                if exp["date"].startswith(current_month):
                    category = exp["category"]
                    amount = float(exp["amount"])
                    monthly_expenses[category] = monthly_expenses.get(category, 0) + amount
            except (ValueError, TypeError):
                continue
        
        # Get user budgets, else use default budgets
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
        
        # Merge: user budgets override default budgets
        budgets = {**default_budgets, **user_budgets}
        
        alerts = []
        for category, spent in monthly_expenses.items():
            budget = budgets.get(category, 5000)  # If category not in budgets, use 5000 as default
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

@app.post("/budgets/{user_id}")
def save_user_budgets(user_id: str, budgets: Dict[str, float]):
    """Save budgets for a user with validation"""
    try:
        # Validate budgets data
        if not isinstance(budgets, dict):
            raise HTTPException(status_code=400, detail="Invalid budgets format")
            
        for category, amount in budgets.items():
            try:
                float(amount)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail=f"Invalid amount for category {category}")
        
        data = load_budgets()
        data[user_id] = budgets
        if save_budgets(data):
            return {"message": "Budgets saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save budgets")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving budgets: {str(e)}")

@app.get("/budgets/{user_id}")
def get_user_budgets(user_id: str):
    """Get budgets for a user with error handling"""
    try:
        data = load_budgets()
        return data.get(user_id, {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading budgets: {str(e)}")

@app.get("/reports/export")
def export_expenses_report(
    user_id: str = "default",
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export expenses in different formats with enhanced error handling"""
    try:
        expenses = get_expenses(user_id)
        
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
                try:
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
                except Exception as e:
                    print(f"Error formatting expense for CSV: {e}")
                    continue
            return {"csv": "\n".join(csv_lines)}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/sample-data/initialize")
def initialize_sample_data_endpoint(user_id: str = "default"):
    """Initialize sample data endpoint with error handling"""
    try:
        success = initialize_sample_data(user_id)
        if success:
            return {"message": "Sample data initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize sample data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample data error: {str(e)}")

@app.post("/users/register")
def register_user(user: UserCreate):
    """Register a new user with enhanced validation"""
    try:
        # Validate input
        if not user.phone_number or not user.phone_number.strip():
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        if not user.password or len(user.password) != 6 or not user.password.isdigit():
            raise HTTPException(status_code=400, detail="Password must be 6 digits")
        
        users = get_users()
        
        # Check if user already exists
        for existing_user in users.values():
            if existing_user["phone_number"] == user.phone_number:
                raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        user_data = {
            "id": str(uuid.uuid4()),
            "phone_number": user.phone_number,
            "password": user.password,  # In production, hash this password
            "created_at": datetime.now().isoformat()
        }
        
        if save_user(user_data):
            # Initialize empty expenses for new user
            save_user_expenses(user_data["id"], [])
            return {"message": "User registered successfully", "user_id": user_data["id"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to register user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.post("/users/login")
def login_user(user: UserCreate):
    """Login user with enhanced validation"""
    try:
        # Validate input
        if not user.phone_number or not user.password:
            raise HTTPException(status_code=400, detail="Phone number and password are required")
        
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
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/users/forgot-password")
def forgot_password(reset_request: PasswordResetRequest):
    """Reset user password with admin code verification"""
    try:
        # Validate admin code
        if reset_request.admin_code != "2139":
            raise HTTPException(status_code=401, detail="Invalid admin code")
        
        # Validate new password
        if not reset_request.new_password or len(reset_request.new_password) != 6 or not reset_request.new_password.isdigit():
            raise HTTPException(status_code=400, detail="New password must be 6 digits")
        
        users = get_users()
        
        # Find user by phone number
        user_found = False
        for user_id, user_data in users.items():
            if user_data["phone_number"] == reset_request.phone_number:
                user_data["password"] = reset_request.new_password
                user_found = True
                break
        
        if not user_found:
            raise HTTPException(status_code=404, detail="User not found")
        
        if save_data(USERS_FILE, users):
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset password")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset error: {str(e)}")

@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get user by ID with error handling"""
    try:
        users = get_users()
        if user_id in users:
            user_data = users[user_id].copy()
            user_data.pop("password", None)  # Don't return password
            return user_data
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.get("/admin/download-db")
def download_database(admin_code: str):
    """Download entire database (admin function)"""
    try:
        # Verify admin code
        if admin_code != "2139":
            raise HTTPException(status_code=401, detail="Invalid admin code")
        
        # Load all data
        expenses_data = load_data(DATA_FILE)
        users_data = get_users()  # This already handles password filtering
        budgets_data = load_budgets()
        
        return {
            "expenses": expenses_data,
            "users": users_data,
            "budgets": budgets_data,
            "exported_at": datetime.now().isoformat(),
            "total_users": len(users_data),
            "total_expense_records": sum(len(expenses) for expenses in expenses_data.values())
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database export error: {str(e)}")

# Initialize sample data when backend starts
try:
    initialize_sample_data()
except Exception as e:
    print(f"Failed to initialize sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
