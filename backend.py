from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid
import os
import json
import random
import asyncio
from groq import Groq
from gtts import gTTS
import io
import base64
import re
import threading
import tempfile
import logging
import aiofiles

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced Expense Tracker API with Tamil Voice Assistant",
    version="3.0.0",
    description="A comprehensive expense tracking system with advanced analytics and Tamil voice assistant"
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
    audio_data: Optional[str] = None
    text_input: Optional[str] = None
    user_id: str = "default"

class AssistantResponse(BaseModel):
    text: str
    audio_base64: Optional[str] = None
    actions: List[Dict[str, Any]] = []
    navigation: Optional[str] = None
    commands_parsed: List[Dict[str, Any]] = []

class ParsedCommand(BaseModel):
    action: str
    entity: str
    details: Dict[str, Any]
    confidence: float

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

manager = ConnectionManager()

# Data Management Functions
def load_data(filename):
    """Load data from JSON file with enhanced error handling"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filename}: {e}")
        try:
            if os.path.exists(filename):
                backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(filename, backup_name)
                logger.info(f"Created backup: {backup_name}")
        except Exception as backup_error:
            logger.error(f"Backup creation failed: {backup_error}")
        return {}
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}

def save_data(filename, data):
    """Save data to JSON file with enhanced error handling"""
    try:
        # Create backup before saving
        if os.path.exists(filename):
            backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(filename, 'r') as source, open(backup_name, 'w') as backup:
                    backup.write(source.read())
            except:
                pass
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
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
            logger.info(f"Cleaned {len(user_expenses) - len(valid_expenses)} invalid expenses for user {user_id}")
        
        return valid_expenses
    except Exception as e:
        logger.error(f"Error getting expenses for user {user_id}: {e}")
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
                logger.warning(f"Skipping invalid expense for user {user_id}: {message}")
        
        data = load_data(DATA_FILE)
        data[user_id] = validated_expenses
        return save_data(DATA_FILE, data)
    except Exception as e:
        logger.error(f"Error saving expenses for user {user_id}: {e}")
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
        logger.error(f"Error loading users: {e}")
        return {}

def save_user(user_data):
    """Save user data with validation"""
    try:
        if not isinstance(user_data, dict) or not user_data.get('phone_number') or not user_data.get('password'):
            logger.error("Invalid user data structure")
            return False
            
        users = get_users()
        users[user_data["id"]] = user_data
        return save_data(USERS_FILE, users)
    except Exception as e:
        logger.error(f"Error saving user: {e}")
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
                        logger.warning(f"Invalid budget amount for {user_id}.{category}: {amount}")
        return valid_budgets
    except Exception as e:
        logger.error(f"Error loading budgets: {e}")
        return {}

def save_budgets(data):
    """Save budgets to JSON file with validation"""
    try:
        if not isinstance(data, dict):
            logger.error("Invalid budgets data structure")
            return False
            
        for user_id, user_budgets in data.items():
            if not isinstance(user_budgets, dict):
                logger.error(f"Invalid user budgets structure for {user_id}")
                return False
                
            for category, amount in user_budgets.items():
                try:
                    float(amount)
                except (ValueError, TypeError):
                    logger.error(f"Invalid budget amount for {user_id}.{category}: {amount}")
                    return False
        
        return save_data(BUDGETS_FILE, data)
    except Exception as e:
        logger.error(f"Error saving budgets: {e}")
        return False

def initialize_sample_data(user_id="default"):
    """Initialize sample data for Chennai computer science student"""
    try:
        existing_expenses = get_expenses(user_id)
        if len(existing_expenses) > 5:
            logger.info(f"Already have {len(existing_expenses)} expenses, skipping sample data")
            return True
        
        logger.info("Initializing sample data...")
        sample_expenses = generate_sample_data()
        
        all_expenses = existing_expenses + sample_expenses
        success = save_user_expenses(user_id, all_expenses)
        
        if success:
            logger.info(f"✅ Sample data initialized successfully with {len(sample_expenses)} expenses")
        else:
            logger.error("❌ Failed to save sample data")
            
        return success
    except Exception as e:
        logger.error(f"❌ Error initializing sample data: {e}")
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
    
    logger.info(f"Generated {expense_count} sample expenses")
    return sample_data

# Tamil Voice Assistant Service
class TamilVoiceAssistant:
    def __init__(self):
        self.groq_client = None
        self.model = os.environ.get("WHISPER_MODEL", "large-v3-turbo")
        
        # Try to initialize Groq client
        try:
            api_key = os.environ.get("GROQ_API_KEY")
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                logger.info("✅ Groq Whisper API initialized successfully")
            else:
                logger.warning("⚠️ GROQ_API_KEY not set. Whisper transcription will use fallback.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
        
        # Tamil-English hybrid patterns
        self.tamil_patterns = {
            "add": ["add", "create", "insert", "பன்னு", "சேர்", "கூட்டு", "add பண்ணு", "create பண்ணு", "சேர்க்க"],
            "update": ["update", "modify", "change", "edit", "மாற்று", "புதுப்பி", "edit பண்ணு", "update பண்ணு"],
            "delete": ["delete", "remove", "erase", "நீக்கு", "அழி", "விடு", "delete பண்ணு", "remove பண்ணு"],
            "read": ["read", "show", "list", "display", "காட்டு", "பார்", "பட்டியல்", "show பண்ணு"],
            "navigate": ["go to", "open", "navigate", "move to", "போ", "திற", "தொகு", "செல்", "காட்டு"],
            "categories": {
                "food": ["food", "சாப்பாடு", "உணவு", "dinner", "lunch", "breakfast", "meals", "food"],
                "travel": ["travel", "பயணம்", "tour", "வழி", "journey", "trip"],
                "transport": ["transport", "போக்குவரத்து", "bus", "auto", "vehicle", "travel"],
                "entertainment": ["entertainment", "மகிழ்வு", "fun", "movie", "cinema", "games"],
                "shopping": ["shopping", "கொள்முதல்", "buy", "purchase", "வாங்கு", "shop"],
                "utilities": ["utilities", "பயன்பாடுகள்", "bill", "internet", "mobile", "electricity"],
                "education": ["education", "கல்வி", "study", "books", "course", "college"],
                "healthcare": ["healthcare", "சுகாதாரம்", "medical", "hospital", "doctor", "medicine"],
                "housing": ["housing", "வீடு", "rent", "hostel", "home", "accommodation"],
                "other": ["other", "மற்றவை", "misc", "general", "சர்வதேச"]
            }
        }
        
        # Page mapping
        self.page_mapping = {
            "dashboard": "Dashboard",
            "analytics": "Analytics",
            "expenses": "Expense List",
            "budgets": "Budgets",
            "export": "Export",
            "add": "Add Expense",
            "voice": "Voice Assistant"
        }

    def transcribe_audio(self, audio_base64: str) -> str:
        """Transcribe audio using Groq Whisper with Tamil support"""
        try:
            if not self.groq_client:
                return "Groq API not configured. Please set GROQ_API_KEY."
            
            # Remove data URL prefix if present
            if audio_base64.startswith('data:audio'):
                audio_base64 = audio_base64.split(',')[1]
            
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            # Transcribe with Groq
            with open(temp_path, 'rb') as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(temp_path, audio_file.read()),
                    model=self.model,
                    language="ta",  # Tamil language code
                    prompt="Transcribe Tamil, English, and Tanglish speech with casual slang. Include food, travel, shopping, expenses related words."
                )
            
            # Clean up
            os.unlink(temp_path)
            logger.info(f"Transcribed text: {transcription.text}")
            return transcription.text.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Fallback: Return a test message
            return "Food 500 add பன்னு, travel 1000 update பண்ணு"

    def parse_tamil_command(self, text: str) -> List[ParsedCommand]:
        """Parse casual Tamil/English/Tanglish commands"""
        commands = []
        text_lower = text.lower().strip()
        
        if not text_lower:
            return commands
        
        logger.info(f"Parsing command: {text_lower}")
        
        # Split by common Tamil separators
        separators = [' ,', ' , ', ',', ' அப்புறம் ', ' then ', ' and ', ' பிறகு ', ' after ', ' next ', ' மற்றும் ']
        parts = [text_lower]
        
        for sep in separators:
            if sep in text_lower:
                parts = [p.strip() for p in text_lower.split(sep) if p.strip()]
                break
        
        logger.info(f"Split into {len(parts)} parts: {parts}")
        
        for part in parts:
            command = self._parse_single_command(part)
            if command:
                commands.append(command)
        
        logger.info(f"Parsed {len(commands)} commands")
        return commands

    def _parse_single_command(self, text: str) -> Optional[ParsedCommand]:
        """Parse a single command"""
        try:
            # Check for navigation first
            if any(nav in text for nav in self.tamil_patterns["navigate"]):
                for page_key, page_name in self.page_mapping.items():
                    if page_key in text:
                        return ParsedCommand(
                            action="navigate",
                            entity="page",
                            details={"page": page_name},
                            confidence=0.9
                        )
            
            # Extract amount (supports ₹ symbol, numbers, etc.)
            amount_patterns = [
                r'₹?\s*(\d+(?:\.\d{1,2})?)',
                r'(\d+)\s*(?:rupees?|ரூபாய்|ரூ)',
                r'amount\s*(\d+)'
            ]
            
            amount = None
            for pattern in amount_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        amount = float(matches[0])
                        break
                    except:
                        continue
            
            # Extract category
            category = None
            for cat_key, cat_patterns in self.tamil_patterns["categories"].items():
                for pattern in cat_patterns:
                    if pattern in text:
                        category = cat_key.capitalize()
                        break
                if category:
                    break
            
            # Determine action
            action = None
            confidence = 0.7
            
            for act_key, act_patterns in self.tamil_patterns.items():
                if act_key in ["categories", "navigate"]:
                    continue
                for pattern in act_patterns:
                    if pattern in text:
                        action = act_key
                        confidence = 0.8
                        break
                if action:
                    break
            
            # If no explicit action but has amount and category, assume add
            if not action and amount and category:
                action = "add"
                confidence = 0.6
            
            # Check for "last" or "recent" references
            has_last = any(word in text for word in ["last", "recent", "final", "கடைசி", "இறுதி"])
            
            entity_type = self._determine_entity(text, has_last)
            if action and entity_type:
                details = {
                    "amount": amount,
                    "category": category or "Other",
                    "description": self._extract_description(text),
                    "date": datetime.now().isoformat(),
                    "is_last": has_last
                }
                
                # Clean up None values
                details = {k: v for k, v in details.items() if v is not None}
                
                return ParsedCommand(
                    action=action,
                    entity=entity_type,
                    details=details,
                    confidence=confidence
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing command '{text}': {e}")
            return None

    def _determine_entity(self, text: str, has_last: bool) -> Optional[str]:
        """Determine if the command is about expense or page"""
        expense_keywords = ["expense", "entry", "record", "transaction", "செலவு", "பதிவு"]
        page_keywords = ["page", "screen", "tab", "section", "பக்கம்", "திரை"]
        
        if any(keyword in text for keyword in expense_keywords):
            return "expense"
        elif any(keyword in text for keyword in page_keywords):
            return "page"
        elif has_last:
            return "expense"
        else:
            # Default to expense for CRUD operations
            return "expense"

    def _extract_description(self, text: str) -> str:
        """Extract description from text"""
        # Remove amounts and common words
        words_to_remove = ["add", "update", "delete", "read", "show", "list", 
                          "for", "to", "the", "a", "an", "my", "me", "please",
                          "பன்னு", "பண்ணு", "காட்டு", "சேர்", "நீக்கு", "மாற்று",
                          "last", "recent", "final", "கடைசி", "இறுதி"]
        
        # Also remove category words
        for category_patterns in self.tamil_patterns["categories"].values():
            words_to_remove.extend(category_patterns)
        
        words = text.split()
        filtered = []
        for w in words:
            w_lower = w.lower()
            # Check if word is a number or contains number
            if re.match(r'^\d+(\.\d+)?$', w_lower):
                continue
            # Check if word is in removal list
            if not any(remove_word in w_lower for remove_word in words_to_remove):
                filtered.append(w)
        
        return " ".join(filtered[:5]) or "Voice expense"

    def text_to_speech_tamil(self, text: str) -> str:
        """Convert text to Tamil speech using gTTS"""
        try:
            if not text.strip():
                return ""
            
            # Create Tamil speech
            tts = gTTS(text=text, lang='ta', slow=False)
            
            # Save to bytes
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            
            # Convert to base64
            return base64.b64encode(audio_bytes.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # Return empty string if TTS fails
            return ""

    async def execute_commands(self, commands: List[ParsedCommand], user_id: str) -> Dict[str, Any]:
        """Execute parsed commands"""
        results = []
        
        for cmd in commands:
            try:
                result = None
                
                if cmd.action == "navigate":
                    result = {
                        "action": "navigate",
                        "page": cmd.details.get("page"),
                        "success": True,
                        "message": f"Navigating to {cmd.details.get('page')}"
                    }
                    
                elif cmd.action == "add":
                    expense_data = {
                        "description": cmd.details.get("description", "Voice expense"),
                        "amount": cmd.details.get("amount", 0.0),
                        "category": cmd.details.get("category", "Other"),
                        "date": datetime.now().isoformat(),
                        "priority": "Medium",
                        "tags": ["voice-assistant", "tamil", cmd.details.get("category", "").lower()],
                        "notes": "Added via Tamil voice command",
                        "id": str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    expenses = get_expenses(user_id)
                    expenses.append(expense_data)
                    
                    if save_user_expenses(user_id, expenses):
                        result = {
                            "action": "add",
                            "amount": cmd.details.get("amount"),
                            "category": cmd.details.get("category"),
                            "description": cmd.details.get("description"),
                            "success": True,
                            "message": f"Added ₹{cmd.details.get('amount')} to {cmd.details.get('category')}"
                        }
                    else:
                        result = {
                            "action": "add",
                            "success": False,
                            "message": "Failed to save expense"
                        }
                
                elif cmd.action == "delete":
                    expenses = get_expenses(user_id)
                    if expenses:
                        if cmd.details.get("is_last"):
                            deleted = expenses.pop()
                            save_user_expenses(user_id, expenses)
                            result = {
                                "action": "delete",
                                "expense": deleted.get("description", "Last expense"),
                                "amount": deleted.get("amount"),
                                "success": True,
                                "message": f"Deleted last expense: {deleted.get('description')}"
                            }
                        else:
                            result = {
                                "action": "delete",
                                "success": False,
                                "message": "Please specify which expense to delete"
                            }
                    else:
                        result = {
                            "action": "delete",
                            "success": False,
                            "message": "No expenses to delete"
                        }
                
                elif cmd.action == "read":
                    expenses = get_expenses(user_id)
                    if expenses:
                        recent = expenses[:5]  # Get 5 most recent
                        total = sum(float(exp.get("amount", 0)) for exp in recent)
                        result = {
                            "action": "read",
                            "count": len(recent),
                            "total": total,
                            "success": True,
                            "message": f"Found {len(recent)} recent expenses totaling ₹{total:.2f}"
                        }
                    else:
                        result = {
                            "action": "read",
                            "success": False,
                            "message": "No expenses found"
                        }
                
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error executing command {cmd}: {e}")
                results.append({
                    "action": cmd.action,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "results": results,
            "total_commands": len(commands),
            "successful": sum(1 for r in results if r.get("success", False))
        }

    def generate_tamil_response(self, results: Dict, original_text: str) -> str:
        """Generate Tamil response text based on execution results"""
        successful = results.get("successful", 0)
        total = results.get("total_commands", 0)
        
        if successful == 0:
            return "மன்னிக்கவும், உங்கள் கட்டளையைப் புரிந்துகொள்ளவோ செயல்படுத்தவோ முடியவில்லை. தயவு செய்து மீண்டும் முயற்சிக்கவும்."
        
        responses = []
        
        for result in results.get("results", []):
            if result.get("success"):
                if result["action"] == "add":
                    responses.append(
                        f"சேர்க்கப்பட்டது ₹{result['amount']} {result['category']} க்கு."
                    )
                elif result["action"] == "delete":
                    responses.append(
                        f"நீக்கப்பட்டது {result['expense']}."
                    )
                elif result["action"] == "navigate":
                    responses.append(
                        f"நகர்த்தப்பட்டது {result['page']} பக்கத்திற்கு."
                    )
                elif result["action"] == "read":
                    responses.append(
                        f"கண்டறியப்பட்டது {result['count']} செலவுகள், மொத்தம் ₹{result['total']:.2f}."
                    )
        
        if len(responses) > 1:
            return f"{len(responses)} செயல்கள் முடிந்தன: {' '.join(responses)}"
        elif responses:
            return responses[0]
        else:
            return "செயல் முடிந்தது. தயவு செய்து தொடரவும்."

# Create assistant instance
assistant = TamilVoiceAssistant()

# WebSocket endpoint for real-time voice processing
@app.websocket("/ws/voice-assistant/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "audio":
                # Send acknowledgment
                await websocket.send_json({
                    "type": "status",
                    "message": "Processing your voice command..."
                })
                
                # Transcribe audio
                transcription = assistant.transcribe_audio(data["audio"])
                
                await websocket.send_json({
                    "type": "transcription",
                    "text": transcription
                })
                
                # Parse commands
                commands = assistant.parse_tamil_command(transcription)
                
                # Execute commands
                results = await assistant.execute_commands(commands, user_id)
                
                # Generate response text in Tamil
                response_text = assistant.generate_tamil_response(results, transcription)
                
                # Generate Tamil voice response
                audio_base64 = assistant.text_to_speech_tamil(response_text)
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "text": response_text,
                    "audio": audio_base64 if audio_base64 else None,
                    "commands": [cmd.dict() for cmd in commands],
                    "results": results,
                    "transcription": transcription
                })
                
            elif data.get("type") == "text":
                # Direct text command
                commands = assistant.parse_tamil_command(data["text"])
                results = await assistant.execute_commands(commands, user_id)
                response_text = assistant.generate_tamil_response(results, data["text"])
                audio_base64 = assistant.text_to_speech_tamil(response_text)
                
                await websocket.send_json({
                    "type": "response",
                    "text": response_text,
                    "audio": audio_base64 if audio_base64 else None,
                    "results": results
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

# REST endpoint for voice processing
@app.post("/voice-assistant/process", response_model=AssistantResponse)
async def process_voice_command(command: VoiceCommand):
    try:
        # If audio provided, transcribe it
        if command.audio_data:
            text = assistant.transcribe_audio(command.audio_data)
        else:
            text = command.text_input
        
        if not text:
            return AssistantResponse(
                text="மன்னிக்கவும், உங்கள் கட்டளையைப் புரிந்துகொள்ள முடியவில்லை.",
                actions=[],
                commands_parsed=[]
            )
        
        # Parse commands
        commands = assistant.parse_tamil_command(text)
        
        if not commands:
            return AssistantResponse(
                text="மன்னிக்கவும், உங்கள் கட்டளையைப் புரிந்துகொள்ள முடியவில்லை. தயவு செய்து மீண்டும் முயற்சிக்கவும்.",
                actions=[],
                commands_parsed=[]
            )
        
        # Execute commands
        results = await assistant.execute_commands(commands, command.user_id)
        
        # Generate Tamil response
        response_text = assistant.generate_tamil_response(results, text)
        
        # Generate Tamil audio
        audio_base64 = assistant.text_to_speech_tamil(response_text)
        
        # Check for navigation
        navigation = None
        for cmd in commands:
            if cmd.action == "navigate":
                navigation = cmd.details.get("page")
                break
        
        return AssistantResponse(
            text=response_text,
            audio_base64=audio_base64,
            actions=results.get("results", []),
            navigation=navigation,
            commands_parsed=[cmd.dict() for cmd in commands]
        )
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice processing error: {str(e)}")

# Audio upload endpoint
@app.post("/voice-assistant/upload-audio")
async def upload_audio(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        # Read audio file
        contents = await file.read()
        audio_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Transcribe
        text = assistant.transcribe_audio(audio_base64)
        
        # Parse and execute commands
        commands = assistant.parse_tamil_command(text)
        results = await assistant.execute_commands(commands, user_id)
        response_text = assistant.generate_tamil_response(results, text)
        audio_base64_response = assistant.text_to_speech_tamil(response_text)
        
        return {
            "transcription": text,
            "response": response_text,
            "audio_response": audio_base64_response,
            "commands": [cmd.dict() for cmd in commands],
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice-assistant/test")
async def test_assistant():
    """Test endpoint for voice assistant"""
    test_commands = [
        "Food 500 add பன்னு",
        "Travel 1000 update பண்ணு",
        "Last expense delete பண்ணு",
        "Analytics கு போ",
        "Show all expenses"
    ]
    
    results = []
    for test_text in test_commands:
        commands = assistant.parse_tamil_command(test_text)
        results.append({
            "test": test_text,
            "parsed_commands": [cmd.dict() for cmd in commands]
        })
    
    return {
        "assistant_status": "active",
        "tamil_support": True,
        "multi_action": True,
        "groq_configured": assistant.groq_client is not None,
        "test_results": results,
        "supported_features": [
            "Tamil/English/Tanglish speech recognition",
            "Multi-command processing in single sentence",
            "CRUD operations via voice",
            "Tamil text-to-speech responses",
            "Navigation commands",
            "Real-time WebSocket support"
        ]
    }

@app.get("/voice-assistant/status")
async def get_assistant_status():
    return {
        "status": "active",
        "version": "3.0.0",
        "tamil_support": True,
        "features": [
            "Tamil/English/Tanglish speech recognition",
            "Multi-command processing",
            "CRUD operations via voice",
            "Tamil text-to-speech",
            "Navigation commands",
            "Real-time WebSocket support",
            "Casual Tamil slang support"
        ],
        "supported_commands": [
            "Category amount add/update/delete பண்ணு",
            "Multiple commands in one sentence",
            "Navigation: Pageக்கு போ",
            "Casual Tamil slang support"
        ],
        "groq_api_available": assistant.groq_client is not None
    }

# Existing endpoints (unchanged except for addition of sample data initialization)
@app.get("/")
def read_root():
    return {
        "message": "Enhanced Expense Tracker API with Tamil Voice Assistant",
        "version": "3.0.0",
        "database": "JSON File",
        "currency": "INR",
        "status": "healthy",
        "voice_assistant": "active"
    }

@app.post("/expenses/", response_model=Expense)
def create_expense(expense: ExpenseCreate, user_id: str = "default"):
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
        
        monthly_trend = [{"month": month, "amount": amount} for month, amount in monthly_data.items()]
        
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
        
        priority_distribution = {}
        for exp in expenses:
            try:
                priority = exp.get("priority", "Medium")
                amount = float(exp["amount"])
                priority_distribution[priority] = priority_distribution.get(priority, 0) + amount
            except (ValueError, TypeError):
                continue
        
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
            spending_velocity = {
                "current_week": 0,
                "previous_week": 0,
                "change_percentage": 0
            }
        
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
        logger.error(f"Error in analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/budgets/alerts")
def get_budget_alerts(user_id: str = "default"):
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
                "category": category,
                "spent": spent,
                "budget": budget,
                "percentage": percentage,
                "alert_level": alert_level
            })
        
        return alerts
    except Exception as e:
        logger.error(f"Error in budget alerts: {e}")
        return []

@app.post("/budgets/{user_id}")
def save_user_budgets(user_id: str, budgets: Dict[str, float]):
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
                    logger.error(f"Error formatting expense for CSV: {e}")
                    continue
            return {"csv": "\n".join(csv_lines)}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/sample-data/initialize")
def initialize_sample_data_endpoint(user_id: str = "default"):
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
    try:
        users = get_users()
        if user_id in users:
            user_data = users[user_id].copy()
            user_data.pop("password", None)
            return user_data
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.get("/admin/download-db")
def download_database(admin_code: str):
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
@app.on_event("startup")
async def startup_event():
    try:
        initialize_sample_data()
        logger.info("✅ Backend started successfully with voice assistant")
    except Exception as e:
        logger.error(f"Failed to initialize sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
