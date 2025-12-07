from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import base64
from io import BytesIO
from gtts import gTTS
import re

app = FastAPI(
    title="Enhanced Expense Tracker API with Voice Assistant",
    version="3.0.0",
    description="A comprehensive expense tracking system with advanced analytics and voice assistant"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable for lazy Groq client initialization
groq_client = None

def get_groq_client():
    """Lazy initialization of Groq client - only create when needed"""
    global groq_client
    if groq_client is None:
        try:
            from groq import Groq
            api_key = os.environ.get("GROQ_API_KEY", "")
            if api_key:
                groq_client = Groq(api_key=api_key)
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            groq_client = None
    return groq_client

# Data storage files
DATA_FILE = "expenses_data.json"
USERS_FILE = "users_data.json"
BUDGETS_FILE = "budgets_data.json"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

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

# Voice Assistant Models
class VoiceTranscriptionRequest(BaseModel):
    audio_base64: str

class VoiceAction(BaseModel):
    type: str
    category: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    id: Optional[str] = None
    page: Optional[str] = None
    status: str = "pending"
    summary: str = ""

class VoiceExecutionResponse(BaseModel):
    transcription: str
    actions: List[VoiceAction]
    confirmations: List[str]
    navigation: Optional[str] = None
    tts_audio_base64: str = ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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

def generate_sample_data():
    """Generate 3 months of sample expense data"""
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

def initialize_sample_data(user_id="default"):
    """Initialize sample data"""
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

# ============================================================================
# VOICE ASSISTANT FUNCTIONS
# ============================================================================

def parse_tamil_voice_command(text: str) -> List[dict]:
    """Parse Tamil/Tanglish voice commands and extract actions"""
    actions = []
    text_lower = text.lower()
    commands = re.split(r'[,;]|அப்புறம்|மற்றும்', text)
    
    category_map = {
        'food': 'Food & Dining', 'உணவு': 'Food & Dining',
        'travel': 'Transportation', 'பயணம்': 'Transportation',
        'transport': 'Transportation', 'shopping': 'Shopping',
        'entertainment': 'Entertainment', 'movie': 'Entertainment',
        'utility': 'Utilities', 'utilities': 'Utilities', 'bill': 'Utilities',
        'education': 'Education', 'course': 'Education',
        'health': 'Healthcare', 'healthcare': 'Healthcare',
        'housing': 'Housing', 'rent': 'Housing',
        'bus': 'Transportation', 'auto': 'Transportation', 'metro': 'Transportation',
    }
    
    for command in commands:
        command = command.strip()
        if not command:
            continue
        action = {"type": "unknown", "status": "pending"}
        numbers = re.findall(r'\d+', command)
        if numbers:
            action["amount"] = float(numbers[0])
        if any(word in command for word in ['add', 'add பண்ணு', 'panna', 'seru']):
            action["type"] = "add"
        elif any(word in command for word in ['update', 'update பண்ணு', 'மாற்று', 'change', 'edit']):
            action["type"] = "update"
        elif any(word in command for word in ['delete', 'remove', 'remove பண்ணு']):
            action["type"] = "delete"
        elif any(word in command for word in ['analytics', 'analytics கு போ', 'dashboard', 'list', 'list காட்டு', 'show', 'view']):
            action["type"] = "navigate"
        for key, value in category_map.items():
            if key in command:
                action["category"] = value
                action["description"] = f"{value} expense"
                break
        if any(word in command for word in ['analytics', 'analytics கு போ']):
            action["page"] = "Analytics"
        elif any(word in command for word in ['dashboard']):
            action["page"] = "Dashboard"
        elif any(word in command for word in ['list', 'list காட்டு', 'view all', 'view']):
            action["page"] = "View All"
        elif any(word in command for word in ['add', 'new expense', 'create']):
            action["page"] = "Add Expense"
        elif any(word in command for word in ['budget']):
            action["page"] = "Budget Manager"
        if action["type"] != "unknown":
            actions.append(action)
    
    return actions if actions else [{"type": "unknown", "status": "failed", "summary": "Could not understand command"}]

def generate_tamil_confirmation(action: dict) -> str:
    """Generate Tamil confirmation message for action"""
    if action["type"] == "add":
        category = action.get("category", "expense").split("&")[0].strip()
        amount = action.get("amount", 0)
        return f"{category} க்கு {amount} ரூபாய் add பண்ணிட்டேன்."
    elif action["type"] == "update":
        amount = action.get("amount", 0)
        return f"Expense {amount} ரூபாய்க்கு update பண்ணிட்டேன்."
    elif action["type"] == "delete":
        return "Last expense delete ஆயிற்று."
    elif action["type"] == "navigate":
        page = action.get("page", "Dashboard")
        return f"{page} பக்கத்திற்கு போ."
    else:
        return "Command execute ஆகலை. மீண்டும் முயற்சி செய்யுங்கள்."

# ============================================================================
# API ENDPOINTS - ROOT
# ============================================================================

@app.get("/")
def read_root():
    client = get_groq_client()
    return {
        "message": "Enhanced Expense Tracker API with Voice Assistant",
        "version": "3.0.0",
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "status": "healthy ✅",
        "voice_assistant": "available" if client else "disabled",
        "groq_configured": client is not None
    }

# ============================================================================
# API ENDPOINTS - EXPENSES (CRUD)
# ============================================================================

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate, user_id: str = "default"):
    """Create a new expense"""
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
    """Get expenses with advanced filtering"""
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
        end_index = skip + limit
        return filtered_expenses[skip:end_index]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")

@app.get("/expenses/{expense_id}", response_model=Expense)
def read_expense(expense_id: str, user_id: str = "default"):
    """Get a specific expense"""
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
    """Update an expense"""
    try:
        expenses = get_expenses(user_id)
        for expense in expenses:
            if expense["id"] == expense_id:
                update_data = expense_update.dict(exclude_unset=True)
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
    """Delete an expense"""
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

# ============================================================================
# API ENDPOINTS - ANALYTICS
# ============================================================================

@app.get("/analytics/overview")
def get_analytics_overview(
    user_id: str = "default",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive analytics"""
    try:
        expenses = get_expenses(user_id)
        if start_date:
            expenses = [exp for exp in expenses if exp["date"] >= start_date]
        if end_date:
            expenses = [exp for exp in expenses if exp["date"] <= end_date]
        if not expenses:
            return AnalyticsResponse(
                total_spent=0, average_daily=0, category_breakdown={},
                monthly_trend=[], weekly_spending=[], priority_distribution={},
                top_expenses=[], daily_pattern={}, spending_velocity={}, savings_rate=0
            ).dict()
        
        total_spent = sum(float(exp["amount"]) for exp in expenses if exp.get("amount"))
        try:
            dates = [datetime.fromisoformat(exp["date"]) for exp in expenses]
            min_date, max_date = min(dates), max(dates)
            days = (max_date - min_date).days + 1
            average_daily = total_spent / days if days > 0 else total_spent
        except:
            average_daily = total_spent / 30
        
        category_breakdown = {}
        for exp in expenses:
            category = exp["category"]
            amount = float(exp.get("amount", 0))
            category_breakdown[category] = category_breakdown.get(category, 0) + amount
        
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
        
        weekly_data = []
        try:
            end_date_obj = max_date if 'max_date' in locals() else datetime.now()
            for i in range(8):
                week_start = end_date_obj - timedelta(days=end_date_obj.weekday() + 7*i)
                week_end = week_start + timedelta(days=6)
                week_amount = sum(
                    float(exp["amount"]) for exp in expenses
                    if datetime.fromisoformat(exp["date"]).date() <= week_end.date()
                    and datetime.fromisoformat(exp["date"]).date() >= week_start.date()
                )
                weekly_data.append({"week": week_start.strftime("%Y-%m-%d"), "amount": week_amount})
            weekly_data.reverse()
        except:
            weekly_data = []
        
        priority_distribution = {}
        for exp in expenses:
            priority = exp.get("priority", "Medium")
            amount = float(exp.get("amount", 0))
            priority_distribution[priority] = priority_distribution.get(priority, 0) + amount
        
        top_expenses = sorted(expenses, key=lambda x: float(x.get("amount", 0)), reverse=True)[:10]
        
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
            last_7_days_spent = sum(
                float(exp["amount"]) for exp in expenses
                if last_7_days_start <= datetime.fromisoformat(exp["date"]).date() <= today
            )
            previous_7_days_spent = sum(
                float(exp["amount"]) for exp in expenses
                if previous_7_days_start <= datetime.fromisoformat(exp["date"]).date() < last_7_days_start
            )
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
            current_month_spent = sum(
                float(exp["amount"]) for exp in expenses
                if exp["date"].startswith(current_month)
            )
            savings_rate = max(0, ((monthly_income - current_month_spent) / monthly_income * 100)) if monthly_income > 0 else 0
        except:
            savings_rate = 0
        
        return AnalyticsResponse(
            total_spent=total_spent, average_daily=average_daily,
            category_breakdown=category_breakdown, monthly_trend=monthly_trend,
            weekly_spending=weekly_data, priority_distribution=priority_distribution,
            top_expenses=top_expenses, daily_pattern=daily_pattern,
            spending_velocity=spending_velocity, savings_rate=savings_rate
        ).dict()
    except Exception as e:
        print(f"Error in analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# ============================================================================
# API ENDPOINTS - BUDGETS
# ============================================================================

@app.get("/budgets/alerts")
def get_budget_alerts(user_id: str = "default"):
    """Get budget alerts"""
    try:
        expenses = get_expenses(user_id)
        current_month = datetime.now().strftime("%Y-%m")
        monthly_expenses = {}
        for exp in expenses:
            if exp["date"].startswith(current_month):
                category = exp["category"]
                amount = float(exp["amount"])
                monthly_expenses[category] = monthly_expenses.get(category, 0) + amount
        
        user_budgets = load_budgets().get(user_id, {})
        default_budgets = {
            "Food & Dining": 6000, "Transportation": 2000, "Entertainment": 1500,
            "Utilities": 1500, "Shopping": 2000, "Healthcare": 1000,
            "Travel": 3000, "Education": 3000, "Housing": 8000, "Other": 2000
        }
        budgets = {**default_budgets, **user_budgets}
        
        alerts = []
        for category, spent in monthly_expenses.items():
            budget = budgets.get(category, 5000)
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
                "category": category, "spent": spent, "budget": budget,
                "percentage": percentage, "alert_level": alert_level
            })
        return alerts
    except Exception as e:
        print(f"Error in budget alerts: {e}")
        return []

@app.post("/budgets/{user_id}")
def save_user_budgets(user_id: str, budgets: Dict[str, float]):
    """Save budgets for a user"""
    try:
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
    """Get budgets for a user"""
    try:
        data = load_budgets()
        return data.get(user_id, {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading budgets: {str(e)}")

# ============================================================================
# API ENDPOINTS - REPORTS
# ============================================================================

@app.get("/reports/export")
def export_expenses_report(
    user_id: str = "default",
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export expenses"""
    try:
        expenses = get_expenses(user_id)
        if start_date:
            expenses = [exp for exp in expenses if exp["date"] >= start_date]
        if end_date:
            expenses = [exp for exp in expenses if exp["date"] <= end_date]
        if format == "json":
            return expenses
        elif format == "csv":
            csv_lines = ["ID,Date,Category,Description,Amount,Priority,Tags,Notes"]
            for exp in expenses:
                try:
                    tags = exp.get("tags", [])
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

# ============================================================================
# API ENDPOINTS - USERS
# ============================================================================

@app.post("/users/register")
def register_user(user: UserCreate):
    """Register a new user"""
    try:
        if not user.phone_number or not user.phone_number.strip():
            raise HTTPException(status_code=400, detail="Phone number is required")
        if not user.password or len(user.password) != 6 or not user.password.isdigit():
            raise HTTPException(status_code=400, detail="Password must be 6 digits")
        users = get_users()
        for existing_user in users.values():
            if existing_user["phone_number"] == user.phone_number:
                raise HTTPException(status_code=400, detail="User already exists")
        user_data = {
            "id": str(uuid.uuid4()),
            "phone_number": user.phone_number,
            "password": user.password,
            "created_at": datetime.now().isoformat()
        }
        if save_user(user_data):
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
    """Login user"""
    try:
        if not user.phone_number or not user.password:
            raise HTTPException(status_code=400, detail="Phone number and password are required")
        users = get_users()
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
    """Reset user password"""
    try:
        if reset_request.admin_code != "2139":
            raise HTTPException(status_code=401, detail="Invalid admin code")
        if not reset_request.new_password or len(reset_request.new_password) != 6 or not reset_request.new_password.isdigit():
            raise HTTPException(status_code=400, detail="New password must be 6 digits")
        users = get_users()
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
    """Get user by ID"""
    try:
        users = get_users()
        if user_id in users:
            user_data = users[user_id].copy()
            user_data.pop("password", None)
            return user_data
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

# ============================================================================
# API ENDPOINTS - VOICE ASSISTANT
# ============================================================================

@app.post("/voice/transcribe")
def transcribe_voice(request: VoiceTranscriptionRequest):
    """Transcribe voice audio using Groq Whisper API"""
    try:
        client = get_groq_client()
        if not client:
            return {"error": "Groq API not configured", "transcription": "Voice feature not available", "status": "unavailable"}
        
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
            with BytesIO(audio_bytes) as audio_file:
                transcript = client.audio.transcriptions.create(
                    file=("audio.wav", audio_file, "audio/wav"),
                    model="whisper-large-v3",
                    language="ta"
                )
            return {"transcription": transcript.text, "status": "success"}
        except Exception as e:
            return {"transcription": f"Transcription error: {str(e)}", "status": "failed"}
    except Exception as e:
        return {"transcription": f"Error: {str(e)}", "status": "failed"}

@app.post("/voice/parse-actions", response_model=List[VoiceAction])
def parse_voice_actions(request_data: dict):
    """Parse transcribed voice text into actionable commands"""
    try:
        text = request_data.get("transcription", "")
        parsed_actions = parse_tamil_voice_command(text)
        
        actions = []
        for action_data in parsed_actions:
            action = VoiceAction(
                type=action_data.get("type", "unknown"),
                category=action_data.get("category"),
                amount=action_data.get("amount"),
                description=action_data.get("description"),
                page=action_data.get("page"),
                status=action_data.get("status", "pending"),
                summary=f"{action_data.get('type', 'unknown')} action"
            )
            actions.append(action)
        
        return actions
    except Exception as e:
        return [VoiceAction(type="error", status="failed", summary=f"Parsing error: {str(e)}")]

@app.post("/voice/execute-actions", response_model=VoiceExecutionResponse)
def execute_voice_actions(
    transcription: str,
    user_id: str = "default",
    category: Optional[str] = None,
    amount: Optional[float] = None,
    description: Optional[str] = None
):
    """Execute parsed voice actions"""
    try:
        parsed_actions = parse_tamil_voice_command(transcription)
        
        actions = []
        confirmations = []
        navigation = None
        
        for action_data in parsed_actions:
            action = VoiceAction(
                type=action_data.get("type"),
                category=action_data.get("category") or category,
                amount=action_data.get("amount") or amount,
                description=action_data.get("description") or description or "Voice expense",
                page=action_data.get("page")
            )
            
            if action.type == "add" and action.amount and action.category:
                try:
                    new_expense = ExpenseCreate(
                        description=action.description or f"{action.category} expense",
                        amount=action.amount,
                        category=action.category,
                        date=datetime.now().isoformat(),
                        priority="Medium",
                        tags=["voice"]
                    )
                    created = create_expense(new_expense, user_id)
                    action.status = "success"
                    action.summary = f"Added ₹{action.amount} to {action.category}"
                except Exception as e:
                    action.status = "failed"
                    action.summary = f"Failed to add expense: {str(e)}"
            
            elif action.type == "delete":
                try:
                    expenses = get_expenses(user_id)
                    if expenses:
                        last_id = expenses[-1]["id"]
                        delete_expense(last_id, user_id)
                        action.status = "success"
                        action.summary = "Last expense deleted"
                    else:
                        action.status = "failed"
                        action.summary = "No expenses to delete"
                except Exception as e:
                    action.status = "failed"
                    action.summary = f"Failed to delete: {str(e)}"
            
            elif action.type == "navigate":
                navigation = action.page or "Dashboard"
                action.status = "success"
                action.summary = f"Navigating to {navigation}"
            
            elif action.type == "list":
                action.type = "navigate"
                navigation = "View All"
                action.status = "success"
                action.summary = "Showing all expenses"
            
            else:
                action.status = "pending"
                action.summary = "Action recognized but not executed"
            
            confirmation = generate_tamil_confirmation({
                "type": action.type,
                "category": action.category,
                "amount": action.amount,
                "page": action.page
            })
            confirmations.append(confirmation)
            actions.append(action)
        
        tts_audio_base64 = ""
        try:
            full_confirmation = " ".join(confirmations)
            tts = gTTS(full_confirmation, lang='ta', slow=False)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            tts_audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        except Exception as e:
            print(f"TTS generation failed: {e}")
        
        return VoiceExecutionResponse(
            transcription=transcription,
            actions=actions,
            confirmations=confirmations,
            navigation=navigation,
            tts_audio_base64=tts_audio_base64
        )
    
    except Exception as e:
        return VoiceExecutionResponse(
            transcription=transcription,
            actions=[],
            confirmations=[f"Error: {str(e)}"],
            navigation=None,
            tts_audio_base64=""
        )

# ============================================================================
# SAMPLE DATA & INITIALIZATION
# ============================================================================

@app.post("/sample-data/initialize")
def initialize_sample_data_endpoint(user_id: str = "default"):
    """Initialize sample data endpoint"""
    try:
        success = initialize_sample_data(user_id)
        if success:
            return {"message": "Sample data initialized successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize sample data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sample data error: {str(e)}")

@app.get("/admin/download-db")
def download_database(admin_code: str):
    """Download entire database (admin function)"""
    try:
        if admin_code != "2139":
            raise HTTPException(status_code=401, detail="Invalid admin code")
        expenses_data = load_data(DATA_FILE)
        users_data = get_users()
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