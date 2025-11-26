import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import base64
import io
from streamlit_mic_recognizer import mic_recognizer
import groq

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")
CURRENCY = "₹"  # Indian Rupee

class EnhancedExpenseTracker:
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.setup_page()
        
    def setup_page(self):
        """Configure Streamlit page settings with enhanced styling"""
        st.set_page_config(
            page_title="💰 Super Expense Tracker Pro + Voice Assistant - INR",
            page_icon="💸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Enhanced CSS with voice assistant styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 0.5rem 0;
        }
        .alert-critical { background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; margin: 5px 0; }
        .alert-warning { background-color: #ffa500; padding: 10px; border-radius: 5px; color: white; margin: 5px 0; }
        .alert-info { background-color: #4b8aff; padding: 10px; border-radius: 5px; color: white; margin: 5px 0; }
        .expense-card { 
            background-color: #f0f2f6; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 10px 0;
            border-left: 5px solid #1f77b4;
        }
        .voice-assistant {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 10px 0;
        }
        .assistant-message {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin: 5px 0;
            border-left: 4px solid #2196f3;
        }
        .user-message {
            background: #f3e5f5;
            padding: 15px;
            border-radius: 10px;
            margin: 5px 0;
            border-left: 4px solid #9c27b0;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem;
            }
            .metric-card {
                padding: 0.5rem;
            }
        }
        
        .stButton button {
            width: 100%;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            margin-top: 50px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<h1 class="main-header">💸 Super Expense Tracker Pro + Voice Assistant - {CURRENCY}</h1>', unsafe_allow_html=True)
    
    def test_connection(self):
        """Test connection to backend with enhanced error handling"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            return response.status_code == 200
        except requests.exceptions.Timeout:
            st.error("⏰ Backend connection timeout")
            return False
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to backend server")
            return False
        except Exception as e:
            st.error(f"🚫 Connection error: {e}")
            return False
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'page' not in st.session_state:
            st.session_state.page = "Dashboard"
        if 'filters' not in st.session_state:
            st.session_state.filters = {}
        if 'edit_expense' not in st.session_state:
            st.session_state.edit_expense = None
        if 'user_id' not in st.session_state:
            st.session_state.user_id = "default"
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'show_account_modal' not in st.session_state:
            st.session_state.show_account_modal = False
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'form_cleared' not in st.session_state:
            st.session_state.form_cleared = False
        if 'date_key' not in st.session_state:
            st.session_state.date_key = 0
        
        # Voice Assistant State
        if 'voice_conversation' not in st.session_state:
            st.session_state.voice_conversation = []
        if 'is_listening' not in st.session_state:
            st.session_state.is_listening = False
        if 'last_audio' not in st.session_state:
            st.session_state.last_audio = None
    
    def render_footer(self):
        """Render footer with tech stack and copyright"""
        st.markdown("""
        <div class="footer">
            <p><strong>Tech Stack:</strong> FastAPI • Streamlit • Plotly • Pandas • Groq AI • Voice Assistant</p>
            <p><strong>Voice Support:</strong> Tamil & English • Multi-CRUD • Natural Language</p>
            <p>© 2024 Expense Tracker Pro. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
    
    def process_voice_command(self, text):
        """Process voice command through backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/voice/process",
                json={
                    "text": text,
                    "user_id": st.session_state.user_id,
                    "language": "ta"
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "text": "Sorry, I couldn't process that command.",
                    "audio_base64": None,
                    "commands": [],
                    "navigation": None
                }
        except Exception as e:
            return {
                "text": f"Error: {str(e)}",
                "audio_base64": None,
                "commands": [],
                "navigation": None
            }
    
    def play_audio_response(self, audio_base64):
        """Play audio response from base64"""
        if audio_base64:
            try:
                audio_bytes = base64.b64decode(audio_base64)
                st.audio(audio_bytes, format='audio/mp3')
                st.session_state.last_audio = audio_bytes
            except Exception as e:
                st.error(f"Audio playback error: {e}")
    
    def render_voice_assistant(self):
        """Render the Tamil/English Voice Assistant interface"""
        st.header("🎤 Voice Assistant - Tamil/English Support")
        
        st.markdown('<div class="voice-assistant">', unsafe_allow_html=True)
        st.subheader("🗣️ Speak Naturally in Tamil or English")
        st.markdown("""
        **Supported Commands:**
        - "Food 200 add பன்னு, travel 150 update பண்ணு" - Multiple operations
        - "200 food, 50 tea, 300 petrol சேர்த்துடு" - Multiple expenses
        - "Analytics கு போ" - Navigation
        - "Last expense delete பண்ணு" - Delete operations
        - "My expenses show பண்ணு" - Read operations
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Voice Input Section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎤 Record Your Command")
            
            # Voice recorder
            audio_text = mic_recognizer(
                start_prompt="🎤 Start Recording (Tamil/English)",
                stop_prompt="⏹️ Stop Recording",
                key="voice_recorder"
            )
            
            if audio_text:
                # Add user message to conversation
                st.session_state.voice_conversation.append({
                    "role": "user",
                    "text": audio_text,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Process the command
                with st.spinner("🔄 Processing your command..."):
                    response = self.process_voice_command(audio_text)
                
                # Add assistant response to conversation
                st.session_state.voice_conversation.append({
                    "role": "assistant",
                    "text": response.get("text", ""),
                    "audio_base64": response.get("audio_base64"),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Handle navigation if specified
                if response.get("navigation"):
                    st.session_state.page = response["navigation"]
                    st.rerun()
        
        with col2:
            st.subheader("⌨️ Text Input")
            text_command = st.text_area(
                "Or type your command:",
                placeholder="e.g., 'Food 200 add pannu, travel 150 update pannu'",
                height=100
            )
            
            if st.button("Send Text Command", use_container_width=True):
                if text_command:
                    # Add user message to conversation
                    st.session_state.voice_conversation.append({
                        "role": "user",
                        "text": text_command,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Process the command
                    with st.spinner("🔄 Processing your command..."):
                        response = self.process_voice_command(text_command)
                    
                    # Add assistant response to conversation
                    st.session_state.voice_conversation.append({
                        "role": "assistant",
                        "text": response.get("text", ""),
                        "audio_base64": response.get("audio_base64"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Handle navigation if specified
                    if response.get("navigation"):
                        st.session_state.page = response["navigation"]
                        st.rerun()
        
        # Conversation History
        st.subheader("💬 Conversation History")
        
        if not st.session_state.voice_conversation:
            st.info("No conversation yet. Start by speaking or typing a command!")
        else:
            for i, message in enumerate(st.session_state.voice_conversation):
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message">👤 <strong>You:</strong> {message["text"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-message">🤖 <strong>Assistant:</strong> {message["text"]}</div>', unsafe_allow_html=True)
                    
                    # Play audio button for assistant responses
                    if message.get("audio_base64"):
                        if st.button(f"🔊 Play Audio Response #{i//2 + 1}", key=f"play_audio_{i}"):
                            self.play_audio_response(message["audio_base64"])
        
        # Quick Action Buttons
        st.subheader("⚡ Quick Voice Commands")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🍽️ Add Food Expense", use_container_width=True):
                st.session_state.voice_conversation.append({
                    "role": "user",
                    "text": "Food 200 rupees add pannu",
                    "timestamp": datetime.now().isoformat()
                })
                response = self.process_voice_command("Food 200 rupees add pannu")
                st.session_state.voice_conversation.append({
                    "role": "assistant",
                    "text": response.get("text", ""),
                    "audio_base64": response.get("audio_base64"),
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()
        
        with col2:
            if st.button("📊 Show Analytics", use_container_width=True):
                st.session_state.page = "Analytics"
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete Last", use_container_width=True):
                st.session_state.voice_conversation.append({
                    "role": "user",
                    "text": "Last expense delete pannu",
                    "timestamp": datetime.now().isoformat()
                })
                response = self.process_voice_command("Last expense delete pannu")
                st.session_state.voice_conversation.append({
                    "role": "assistant",
                    "text": response.get("text", ""),
                    "audio_base64": response.get("audio_base64"),
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()
        
        with col4:
            if st.button("🔄 Clear Chat", use_container_width=True):
                st.session_state.voice_conversation = []
                st.rerun()
    
    def render_sidebar(self):
        """Render enhanced sidebar with navigation and quick stats"""
        with st.sidebar:
            st.markdown("## 🧭 Navigation")
            
            # Navigation buttons
            pages = {
                "📊 Dashboard": "Dashboard",
                "➕ Add Expense": "Add Expense", 
                "📋 Expense List": "Expense List",
                "📈 Analytics": "Analytics",
                "💰 Budgets": "Budgets",
                "📤 Export": "Export",
                "🎤 Voice Assistant": "Voice Assistant"
            }
            
            for icon, page in pages.items():
                if st.button(icon, key=page, use_container_width=True):
                    st.session_state.page = page
            
            st.markdown("---")
            st.markdown("## ⚡ Quick Stats")
            
            # Display quick stats
            try:
                analytics = self.get_analytics()
                if analytics:
                    st.metric("Total Spent", f"{CURRENCY}{analytics.get('total_spent', 0):,.0f}")
                    st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):.0f}")
                    st.metric("Savings Rate", f"{analytics.get('savings_rate', 0):.1f}%")
                    
                    # Weekly comparison
                    velocity = analytics.get('spending_velocity', {})
                    if velocity:
                        change = velocity.get('change_percentage', 0)
                        st.metric("Weekly Trend", f"{CURRENCY}{velocity.get('current_week', 0):.0f}", 
                                 delta=f"{change:+.1f}%")
            except Exception as e:
                st.info("Connect to backend to see stats")
            
            st.markdown("---")
            
            # Voice Assistant Quick Access
            st.markdown("## 🎤 Voice Assistant")
            if st.button("🎤 Start Voice Command", use_container_width=True):
                st.session_state.page = "Voice Assistant"
                st.rerun()
            
            st.markdown("---")
            
            # Account management
            if st.button("👤 Go to My Account", use_container_width=True):
                st.session_state.show_account_modal = True
                st.rerun()
            
            if st.session_state.logged_in and st.session_state.user_id != "default":
                st.info(f"🔐 Logged in as: {st.session_state.user_id[:8]}...")
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.logged_in = False
                    st.session_state.user_id = "default"
                    st.rerun()

    # ... (All other existing methods from the previous frontend.py remain exactly the same)
    # The render_dashboard, render_add_expense, render_expense_list, render_analytics, 
    # render_budgets, render_export, and other methods continue unchanged...
    
    def run(self):
        """Main method to run the enhanced application with voice assistant"""
        # Check backend connection
        if not self.test_connection():
            st.error("🚫 Cannot connect to backend server. Please make sure the FastAPI server is running")
            st.info("💡 Backend URL: " + self.backend_url)
            if st.button("🔄 Retry Connection"):
                st.rerun()
            return
        
        # Initialize session state
        self.initialize_session_state()
        
        # Render account modal if needed
        if st.session_state.show_account_modal:
            self.render_account_modal()
            return
        
        # Render sidebar
        self.render_sidebar()
        
        # Render main content based on current page
        if st.session_state.page == "Dashboard":
            self.render_dashboard()
        elif st.session_state.page == "Add Expense":
            self.render_add_expense()
        elif st.session_state.page == "Expense List":
            self.render_expense_list()
        elif st.session_state.page == "Analytics":
            self.render_analytics()
        elif st.session_state.page == "Budgets":
            self.render_budgets()
        elif st.session_state.page == "Export":
            self.render_export()
        elif st.session_state.page == "Voice Assistant":
            self.render_voice_assistant()
        
        # Render footer
        self.render_footer()

# Run the application
if __name__ == "__main__":
    app = EnhancedExpenseTracker(BACKEND_URL)
    app.run()
