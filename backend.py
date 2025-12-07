from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import io
import base64
import wave
import numpy as np
from groq import Groq
from gtts import gTTS

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

# Data storage files
DATA_FILE = "expenses_data.json"
USERS_FILE = "users_data.json"
BUDGETS_FILE = "budgets_data.json"

# Initialize Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

# ==================== MODELS ====================

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

class VoiceTranscribeRequest(BaseModel):
    audio_base64: str

class VoiceActionRequest(BaseModel):
    transcription: str

class VoiceActionResponse(BaseModel):
    transcription: str
    actions: List[Dict[str, Any]]
    confirmations: List[str]
    navigation: Optional[str] = None
    tts_base64: Optional[str] = None

# ==================== UTILITY FUNCTIONS ====================

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

# ==================== ROOT ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API with Voice Assistant is running",
        "version": "3.0.0",
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "status": "healthy",
        "voice_assistant": "enabled" if groq_client else "disabled (no GROQ_API_KEY)"
    }

# ==================== EXPENSE CRUD ENDPOINTS (UNCHANGED) ====================

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

# ==================== ANALYTICS ENDPOINTS (UNCHANGED) ====================

@app.get("/analytics/overview")
def get_analytics_overview(
    user_id: str = "default",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive analytics with enhanced error handling"""
    try:
        expenses = get_expenses(user_id)
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

        total_spent = 0
        for exp in expenses:
            try:
                total_spent += float(exp["amount"])
            except (ValueError, TypeError):
                continue

        try:
            dates = [datetime.fromisoformat(exp["date"]) for exp in expenses]
            min_date = min(dates)
            max_date = max(dates)
            days = (max_date - min_date).days + 1
            average_daily = total_spent / days if days > 0 else total_spent
        except:
            average_daily = total_spent / 30

        category_breakdown = {}
        for exp in expenses:
            try:
                category = exp["category"]
                amount = float(exp["amount"])
                category_breakdown[category] = category_breakdown.get(category, 0) + amount
            except (ValueError, TypeError):
                continue

        monthly_data = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                month_key = date.strftime("%Y-%m")
                amount = float(exp["amount"])
                monthly_data[month_key] = monthly_data.get(month_key, 0) + amount
            except:
                continue
        monthly_trend = [{"month": month, "amount": amount} for month, amount in sorted(monthly_data.items())]

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
                weekly_data.append({"week": week_start.strftime("%Y-%m-%d"), "amount": week_amount})
            weekly_data.reverse()
        except:
            weekly_data = []

        priority_distribution = {}
        for exp in expenses:
            priority = exp.get("priority", "Medium")
            try:
                amount = float(exp["amount"])
                priority_distribution[priority] = priority_distribution.get(priority, 0) + amount
            except (ValueError, TypeError):
                continue

        top_expenses = []
        try:
            sorted_expenses = sorted(expenses, key=lambda x: float(x.get("amount", 0)), reverse=True)[:5]
            top_expenses = [
                {
                    "description": exp["description"],
                    "amount": float(exp["amount"]),
                    "category": exp["category"],
                    "date": exp["date"]
                } for exp in sorted_expenses
            ]
        except:
            pass

        daily_pattern = {}
        for exp in expenses:
            try:
                date = datetime.fromisoformat(exp["date"])
                day_name = date.strftime("%A")
                amount = float(exp["amount"])
                daily_pattern[day_name] = daily_pattern.get(day_name, 0) + amount
            except:
                continue

        spending_velocity = {}
        try:
            current_month = datetime.now().strftime("%Y-%m")
            current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            
            for exp in expenses:
                exp_date = datetime.fromisoformat(exp["date"])
                exp_month = exp_date.strftime("%Y-%m")
                exp_week_start = exp_date - timedelta(days=exp_date.weekday())
                
                if exp_month == current_month:
                    spending_velocity["this_month"] = spending_velocity.get("this_month", 0) + float(exp.get("amount", 0))
                if exp_week_start == current_week_start.date():
                    spending_velocity["this_week"] = spending_velocity.get("this_week", 0) + float(exp.get("amount", 0))
        except:
            pass

        savings_rate = 0
        try:
            if total_spent > 0:
                savings_rate = min(100, max(0, (1 - (total_spent / (total_spent + 1000))) * 100))
        except:
            pass

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
        raise HTTPException(status_code=500, detail=f"Error calculating analytics: {str(e)}")

# ==================== VOICE ASSISTANT ENDPOINTS ====================

@app.post("/voice/transcribe")
def transcribe_audio(request: VoiceTranscribeRequest, user_id: str = "default"):
    """Transcribe audio using Groq Whisper API"""
    try:
        if not groq_client:
            raise HTTPException(status_code=400, detail="GROQ_API_KEY not configured")

        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Create temporary WAV file in memory
        audio_io = io.BytesIO()
        with wave.open(audio_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_bytes)
        
        audio_io.seek(0)
        
        # Transcribe using Groq
        with audio_io as audio_file:
            transcript = groq_client.audio.transcriptions.create(
                file=("audio.wav", audio_file, "audio/wav"),
                model="whisper-large-v3",
                language="ta"  # Tamil language
            )
        
        return {
            "transcription": transcript.text,
            "language": "ta",
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/voice/parse-actions")
def parse_voice_actions(request: VoiceActionRequest, user_id: str = "default"):
    """Parse Tamil/Tanglish voice input and extract actions"""
    try:
        text = request.transcription.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Empty transcription")

        actions = []
        confirmations = []
        navigation_target = None

        # Split by common separators
        action_strings = []
        for sep in [',', 'அப்புறம்', 'and']:
            if sep in text:
                parts = text.split(sep)
                action_strings.extend([p.strip() for p in parts if p.strip()])
                break
        
        if not action_strings:
            action_strings = [text]

        # Parse each action
        for action_str in action_strings:
            action_str_lower = action_str.lower()

            # Navigation commands
            if 'analytics' in action_str_lower or 'analytics கு போ' in action_str_lower:
                navigation_target = "Analytics"
                confirmations.append("Analytics page கு போயிட்டேன்.")
                continue
            elif 'dashboard' in action_str_lower or 'dashboard காட்டு' in action_str_lower:
                navigation_target = "Dashboard"
                confirmations.append("Dashboard கு போயிட்டேன்.")
                continue
            elif ('list' in action_str_lower or 'list காட்டு' in action_str_lower or 
                  'எதெல்லாம் இருக்கு' in action_str_lower):
                navigation_target = "View All"
                confirmations.append("Expense list காட்டிட்டேன்.")
                continue

            # Extract category and amount
            category = None
            amount = None
            
            # Common categories in Tamil and English
            categories = {
                'food': 'Food & Dining', 'உணவு': 'Food & Dining', 'சாப்பாடு': 'Food & Dining',
                'travel': 'Transportation', 'பயணம்': 'Transportation', 'வாகனம்': 'Transportation',
                'auto': 'Transportation', 'bus': 'Transportation',
                'entertainment': 'Entertainment', 'cinema': 'Entertainment', 'movie': 'Entertainment',
                'education': 'Education', 'படிப்பு': 'Education', 'கல்வி': 'Education',
                'books': 'Education', 'புத்தகம்': 'Education',
                'utilities': 'Utilities', 'மின்சாரம்': 'Utilities', 'water': 'Utilities',
                'housing': 'Housing', 'வாடை': 'Housing', 'rent': 'Housing',
                'health': 'Healthcare', 'மருத்துவம்': 'Healthcare',
                'shopping': 'Entertainment', 'வாங்குவது': 'Entertainment',
            }

            # Extract category
            for key, val in categories.items():
                if key in action_str_lower:
                    category = val
                    break

            # Extract amount
            import re
            amount_pattern = r'(\d+(?:\.\d{1,2})?)'
            amount_matches = re.findall(amount_pattern, action_str)
            if amount_matches:
                amount = float(amount_matches[0])

            # Determine action type
            action_type = None
            tamil_action_keyword = None

            if any(kw in action_str_lower for kw in ['add பண்ணு', 'add செய்', 'add செரு', 'add panna', 'add']):
                action_type = "add"
                tamil_action_keyword = "add பண்ணிட்டேன்"
            elif any(kw in action_str_lower for kw in ['update பண்ணு', 'மாற்று', 'change பண்ணு', 'update']):
                action_type = "update"
                tamil_action_keyword = "update பண்ணிட்டேன்"
            elif any(kw in action_str_lower for kw in ['delete பண்ணு', 'remove பண்ணு', 'last entry delete', 'delete']):
                action_type = "delete"
                tamil_action_keyword = "delete ஆயிற்று"

            if action_type and category and amount:
                actions.append({
                    "type": action_type,
                    "category": category,
                    "amount": amount,
                    "status": "pending"
                })
                confirmation_text = f"{category} ₹{amount} {tamil_action_keyword}."
                confirmations.append(confirmation_text)
            elif action_type == "delete":
                actions.append({
                    "type": "delete",
                    "category": None,
                    "amount": None,
                    "status": "pending"
                })
                confirmations.append("Last entry delete ஆயிற்று.")

        return {
            "transcription": text,
            "actions": actions,
            "confirmations": confirmations,
            "navigation": navigation_target,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Parse error: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

@app.post("/voice/execute-actions")
def execute_voice_actions(request: VoiceActionRequest, user_id: str = "default"):
    """Execute parsed actions using existing APIs"""
    try:
        text = request.transcription.strip()
        
        # First parse actions
        parse_response = parse_voice_actions(request, user_id)
        actions = parse_response.get("actions", [])
        confirmations = parse_response.get("confirmations", [])
        navigation_target = parse_response.get("navigation")

        executed_actions = []
        expenses = get_expenses(user_id)

        # Execute each action
        for action in actions:
            action_type = action.get("type")
            category = action.get("category")
            amount = action.get("amount")

            if action_type == "add" and category and amount:
                try:
                    new_expense = {
                        "id": str(uuid.uuid4()),
                        "description": category,
                        "amount": amount,
                        "category": category,
                        "date": datetime.now().date().isoformat(),
                        "priority": "Medium",
                        "tags": ["voice"],
                        "notes": "Added via voice assistant",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    expenses.append(new_expense)
                    executed_actions.append({
                        "type": "add",
                        "status": "success",
                        "summary": f"Added {category} expense ₹{amount}"
                    })
                except Exception as e:
                    executed_actions.append({
                        "type": "add",
                        "status": "failed",
                        "summary": str(e)
                    })

            elif action_type == "delete":
                try:
                    if expenses:
                        deleted = expenses.pop()
                        executed_actions.append({
                            "type": "delete",
                            "status": "success",
                            "summary": f"Deleted last expense: {deleted.get('description')}"
                        })
                    else:
                        executed_actions.append({
                            "type": "delete",
                            "status": "failed",
                            "summary": "No expenses to delete"
                        })
                except Exception as e:
                    executed_actions.append({
                        "type": "delete",
                        "status": "failed",
                        "summary": str(e)
                    })

            elif action_type == "update" and category and amount:
                try:
                    if expenses:
                        expenses[-1]["amount"] = amount
                        expenses[-1]["updated_at"] = datetime.now().isoformat()
                        executed_actions.append({
                            "type": "update",
                            "status": "success",
                            "summary": f"Updated expense to ₹{amount}"
                        })
                    else:
                        executed_actions.append({
                            "type": "update",
                            "status": "failed",
                            "summary": "No expenses to update"
                        })
                except Exception as e:
                    executed_actions.append({
                        "type": "update",
                        "status": "failed",
                        "summary": str(e)
                    })

        # Save updated expenses
        save_user_expenses(user_id, expenses)

        # Generate TTS confirmation
        tts_base64 = None
        try:
            if confirmations:
                confirmation_text = " ".join(confirmations)
                tts = gTTS(text=confirmation_text, lang='ta', slow=False)
                tts_io = io.BytesIO()
                tts.write_to_fp(tts_io)
                tts_io.seek(0)
                tts_base64 = base64.b64encode(tts_io.read()).decode('utf-8')
        except Exception as e:
            print(f"TTS generation error: {e}")

        return VoiceActionResponse(
            transcription=text,
            actions=executed_actions,
            confirmations=confirmations,
            navigation=navigation_target,
            tts_base64=tts_base64
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")

# ==================== BUDGET ENDPOINTS (UNCHANGED) ====================

@app.get("/budgets/")
def get_budgets(user_id: str = "default"):
    """Get all budgets for a user"""
    try:
        budgets = load_budgets()
        return budgets.get(user_id, {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budgets: {str(e)}")

@app.post("/budgets/")
def set_budget(budgets_data: Dict[str, float], user_id: str = "default"):
    """Set budgets for a user"""
    try:
        budgets = load_budgets()
        budgets[user_id] = budgets_data
        if save_budgets(budgets):
            return {"message": "Budgets updated successfully", "budgets": budgets_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to save budgets")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting budgets: {str(e)}")

@app.get("/budget-alerts/")
def get_budget_alerts(user_id: str = "default"):
    """Get budget alerts"""
    try:
        expenses = get_expenses(user_id)
        budgets = load_budgets().get(user_id, {})
        alerts = []

        category_spending = {}
        for exp in expenses:
            category = exp.get("category", "Other")
            amount = float(exp.get("amount", 0))
            category_spending[category] = category_spending.get(category, 0) + amount

        for category, budget_amount in budgets.items():
            spent = category_spending.get(category, 0)
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
            
            if percentage >= 80:
                alert_level = "critical" if percentage >= 100 else "warning"
                alerts.append({
                    "category": category,
                    "spent": spent,
                    "budget": budget_amount,
                    "percentage": percentage,
                    "alert_level": alert_level
                })

        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budget alerts: {str(e)}")

# ==================== USER ENDPOINTS (UNCHANGED) ====================

@app.post("/users/")
def create_user(user: UserCreate):
    """Create a new user"""
    try:
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "phone_number": user.phone_number,
            "password": user.password,
            "created_at": datetime.now().isoformat()
        }
        if save_user(user_data):
            return {"message": "User created successfully", "user_id": user_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/users/")
def list_users():
    """List all users (admin only)"""
    try:
        users = get_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.post("/password-reset/")
def reset_password(request: PasswordResetRequest):
    """Reset user password"""
    try:
        users = get_users()
        for user_id, user_data in users.items():
            if user_data.get("phone_number") == request.phone_number:
                if request.admin_code == "ADMIN_SECRET_CODE":
                    user_data["password"] = request.new_password
                    if save_user(user_data):
                        return {"message": "Password reset successfully"}
                    else:
                        raise HTTPException(status_code=500, detail="Failed to reset password")
                else:
                    raise HTTPException(status_code=401, detail="Invalid admin code")
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")

# ==================== INITIALIZATION ====================

@app.on_event("startup")
def startup_event():
    """Initialize app on startup"""
    print("🚀 Expense Tracker API starting up...")
    initialize_sample_data()
    print("✅ API ready")
