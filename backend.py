from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import groq
from gtts import gTTS
import io
import base64

app = FastAPI(
    title="Enhanced Expense Tracker API with Voice Assistant",
    version="3.0.0",
    description="A comprehensive expense tracking system with advanced analytics and Tamil/English voice assistant"
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
VOICE_SESSIONS_FILE = "voice_sessions.json"

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
    text: str
    user_id: str = "default"
    language: str = "ta"  # Tamil by default

class VoiceResponse(BaseModel):
    text: str
    audio_base64: Optional[str] = None
    commands: List[Dict[str, Any]] = []
    navigation: Optional[str] = None

# Initialize Groq client
groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY", "gsk_test_key"))

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

def text_to_speech(text, language="ta"):
    """Convert text to speech and return base64 audio"""
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return None

def parse_voice_command(command_text, user_id="default"):
    """Parse natural language command using Groq LLM"""
    try:
        # Get user's expenses for context
        expenses = get_expenses(user_id)
        recent_expenses = expenses[-5:] if expenses else []
        
        system_prompt = """
        You are a Tamil-English bilingual expense tracker assistant. Parse the user's casual speech into structured JSON commands.
        
        SUPPORTED OPERATIONS:
        - ADD: Add one or multiple expenses
        - UPDATE: Update existing expenses  
        - DELETE: Delete expenses
        - READ: List/search expenses
        - NAVIGATE: Change app pages
        
        RESPONSE FORMAT:
        {
            "response_text": "Tamil/English confirmation message",
            "commands": [
                {
                    "operation": "ADD/UPDATE/DELETE/READ",
                    "details": { ... }
                }
            ],
            "navigation": "Dashboard/Add Expense/Expense List/Analytics/Budgets/Export/Voice Assistant"
        }
        
        TAMIL EXAMPLES:
        - "Food 200 add பன்னு, travel 150 update பண்ணு, last entry delete பண்ணு." → Multiple operations
        - "200 food, 50 tea, 300 petrol சேர்த்துடு." → Multiple adds
        - "Analytics கு போ" → Navigation to Analytics
        - "last expense delete பண்ணு" → Delete last expense
        
        ENGLISH EXAMPLES:  
        - "Add food 200 rupees" → Single add
        - "Show me my expenses" → Read operation
        - "Go to dashboard" → Navigation
        
        Always provide friendly, conversational responses in Tamil/English mix.
        """
        
        user_context = f"""
        User Command: {command_text}
        
        Recent Expenses (for reference):
        {json.dumps(recent_expenses, indent=2) if recent_expenses else "No recent expenses"}
        
        Current Date: {datetime.now().isoformat()}
        """
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        response = json.loads(chat_completion.choices[0].message.content)
        return response
        
    except Exception as e:
        print(f"Error parsing voice command: {e}")
        return {
            "response_text": "Sorry, I couldn't understand that. Please try again.",
            "commands": [],
            "navigation": None
        }

def execute_voice_commands(commands, user_id="default"):
    """Execute parsed voice commands"""
    results = []
    
    for command in commands:
        try:
            operation = command.get("operation", "").upper()
            details = command.get("details", {})
            
            if operation == "ADD":
                # Handle single or multiple adds
                expenses_to_add = details.get("expenses", [details])
                
                for expense_data in expenses_to_add:
                    # Ensure required fields
                    if "description" not in expense_data:
                        expense_data["description"] = f"{expense_data.get('category', 'Expense')} expense"
                    
                    if "date" not in expense_data:
                        expense_data["date"] = datetime.now().date().isoformat()
                    
                    if "priority" not in expense_data:
                        expense_data["priority"] = "Medium"
                    
                    # Create expense
                    expense_payload = {
                        "description": expense_data["description"],
                        "amount": float(expense_data["amount"]),
                        "category": expense_data["category"],
                        "date": expense_data["date"],
                        "priority": expense_data["priority"],
                        "tags": expense_data.get("tags", []),
                        "notes": expense_data.get("notes")
                    }
                    
                    expenses = get_expenses(user_id)
                    expense_data = {
                        **expense_payload,
                        "id": str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    expenses.append(expense_data)
                    if save_user_expenses(user_id, expenses):
                        results.append(f"Added ₹{expense_data['amount']} to {expense_data['category']}")
                    else:
                        results.append(f"Failed to add expense: {expense_data['category']}")
            
            elif operation == "UPDATE":
                expense_id = details.get("id")
                updates = details.get("updates", {})
                
                expenses = get_expenses(user_id)
                for expense in expenses:
                    if expense["id"] == expense_id or (expense_id == "last" and expense == expenses[-1]):
                        expense.update(updates)
                        expense["updated_at"] = datetime.now().isoformat()
                        break
                
                if save_user_expenses(user_id, expenses):
                    results.append(f"Updated expense: {details.get('description', 'Unknown')}")
                else:
                    results.append("Failed to update expense")
            
            elif operation == "DELETE":
                expense_id = details.get("id")
                
                expenses = get_expenses(user_id)
                if expense_id == "last" and expenses:
                    deleted = expenses.pop()
                    if save_user_expenses(user_id, expenses):
                        results.append(f"Deleted expense: {deleted['description']} - ₹{deleted['amount']}")
                    else:
                        results.append("Failed to delete expense")
                else:
                    # Delete by ID
                    new_expenses = [e for e in expenses if e["id"] != expense_id]
                    if len(new_expenses) < len(expenses):
                        if save_user_expenses(user_id, new_expenses):
                            results.append("Expense deleted successfully")
                        else:
                            results.append("Failed to delete expense")
                    else:
                        results.append("Expense not found")
            
            elif operation == "READ":
                # Return expense list for display
                filters = details.get("filters", {})
                filtered_expenses = get_expenses(user_id)
                
                # Apply basic filters
                if filters.get("category"):
                    filtered_expenses = [e for e in filtered_expenses if e["category"] == filters["category"]]
                if filters.get("min_amount"):
                    filtered_expenses = [e for e in filtered_expenses if float(e["amount"]) >= filters["min_amount"]]
                
                if filtered_expenses:
                    summary = f"Found {len(filtered_expenses)} expenses. Total: ₹{sum(float(e['amount']) for e in filtered_expenses):.2f}"
                    results.append(summary)
                else:
                    results.append("No expenses found matching your criteria")
        
        except Exception as e:
            results.append(f"Error executing {operation}: {str(e)}")
    
    return results

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

# Existing endpoints remain the same until we add new voice endpoints...

@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API with Voice Assistant is running",
        "version": "3.0.0",
        "database": "JSON File (Render Compatible)",
        "currency": "INR",
        "voice_assistant": "Tamil/English Support",
        "status": "healthy"
    }

# ... (All existing endpoints from previous backend.py remain exactly the same)

@app.post("/voice/process")
async def process_voice_command(voice_command: VoiceCommand):
    """Process voice commands with Tamil/English support"""
    try:
        # Parse the voice command
        parsed_response = parse_voice_command(voice_command.text, voice_command.user_id)
        
        # Execute commands if any
        execution_results = []
        if parsed_response.get("commands"):
            execution_results = execute_voice_commands(
                parsed_response["commands"], 
                voice_command.user_id
            )
        
        # Combine response text with execution results
        response_text = parsed_response.get("response_text", "I've processed your request.")
        if execution_results:
            response_text += "\n\n" + "\n".join(execution_results)
        
        # Generate audio response
        audio_base64 = text_to_speech(response_text, voice_command.language)
        
        return VoiceResponse(
            text=response_text,
            audio_base64=audio_base64,
            commands=parsed_response.get("commands", []),
            navigation=parsed_response.get("navigation")
        )
        
    except Exception as e:
        error_text = "Sorry, I encountered an error processing your request."
        audio_base64 = text_to_speech(error_text, voice_command.language)
        
        return VoiceResponse(
            text=error_text,
            audio_base64=audio_base64,
            commands=[],
            navigation=None
        )

@app.post("/voice/transcribe")
async def transcribe_audio(audio_file: bytes):
    """Transcribe audio using Groq Whisper (placeholder - implement actual Whisper)"""
    try:
        # In a real implementation, you would send audio to Whisper API
        # For now, return a placeholder
        return {
            "text": "Audio transcription would appear here",
            "language": "ta"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

# Initialize sample data when backend starts
try:
    initialize_sample_data()
except Exception as e:
    print(f"Failed to initialize sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
