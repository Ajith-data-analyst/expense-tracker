import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import base64
import asyncio
import websockets
import queue
import threading
import time
import streamlit.components.v1 as components
import io
from gtts import gTTS
import tempfile
import numpy as np

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")
CURRENCY = "₹"

class TamilVoiceAssistantUI:
    """Advanced Tamil Voice Assistant Interface"""
    
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.ws_url = backend_url.replace("https://", "wss://").replace("http://", "ws://")
        self.websocket = None
        self.is_connected = False
        self.audio_queue = queue.Queue()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup assistant UI with Tamil styling"""
        st.markdown("""
        <style>
        .assistant-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .tamil-title {
            font-family: 'Arial Unicode MS', 'Noto Sans Tamil', sans-serif;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .voice-bubble {
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            border-radius: 25px 25px 25px 0;
            margin: 10px 0;
            max-width: 80%;
            animation: slideIn 0.3s ease;
        }
        
        .assistant-bubble {
            background: #2196F3;
            color: white;
            padding: 15px 20px;
            border-radius: 25px 25px 0 25px;
            margin: 10px 0;
            max-width: 80%;
            margin-left: auto;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .pulse-animation {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .voice-btn {
            background: linear-gradient(45deg, #FF416C, #FF4B2B);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 10px auto;
        }
        
        .voice-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(255, 65, 108, 0.3);
        }
        
        .command-examples {
            background: #f8f9fa;
            border-left: 5px solid #2196F3;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .example-item {
            padding: 5px 0;
            color: #555;
            font-family: 'Courier New', monospace;
        }
        
        .action-badge {
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 2px;
        }
        
        .audio-player {
            width: 100%;
            margin: 10px 0;
        }
        
        .conversation-box {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f5f7fa;
            border-radius: 15px;
            margin: 20px 0;
            border: 1px solid #ddd;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-connected {
            background-color: #4CAF50;
            box-shadow: 0 0 10px #4CAF50;
        }
        
        .status-disconnected {
            background-color: #f44336;
        }
        
        .voice-input-section {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
        }
        
        .feature-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render Tamil voice assistant header"""
        st.markdown("""
        <div class="assistant-header">
            <h1 class="tamil-title">🗣️ தமிழ் குரு உதவியாளர்</h1>
            <p>பேச்சு மூலம் செலவுகளை நிர்வகிக்கவும் | Manage expenses with voice</p>
            <div style="margin-top: 20px;">
                <span class="action-badge">Tamil</span>
                <span class="action-badge">English</span>
                <span class="action-badge">Tanglish</span>
                <span class="action-badge">Multi-Command</span>
                <span class="action-badge">Voice Feedback</span>
                <span class="action-badge">CRUD Operations</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_command_examples(self):
        """Show example Tamil commands"""
        with st.expander("📚 எடுத்துக்காட்டு கட்டளைகள் | Example Commands", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **செலவு சேர்க்க:**
                <div class="example-item">• Food 500 add பன்னு</div>
                <div class="example-item">• Travel 1000 add பண்ணு</div>
                <div class="example-item">• Shopping 2000 சேர்</div>
                <div class="example-item">• ஃபுட் 500 add பன்னு</div>
                <div class="example-item">• ட்ராவல் 1000 update பண்ணு</div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                **பக்கத்திற்கு செல்ல:**
                <div class="example-item">• Analytics கு போ</div>
                <div class="example-item">• Dashboard காட்டு</div>
                <div class="example-item">• Budgets open பண்ணு</div>
                <div class="example-item">• Add expense page show</div>
                <div class="example-item">• Export page open பண்ணு</div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                **பல கட்டளைகள் ஒரே நேரத்தில்:**
                <div class="example-item">• Food 200 add, Travel 300 update பண்ணு</div>
                <div class="example-item">• Last expense delete பண்ணு, new expense add பண்ணு</div>
                <div class="example-item">• Show all expenses, then add food 500</div>
                <div class="example-item">• Food 500 add, travel 800 add, shopping 1200 add</div>
                <div class="example-item">• கடைசி செலவு delete பண்ணு, புது செலவு add பண்ணு</div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                **கேஷுவல் டாமில்/தமிழில்:**
                <div class="example-item">• ஃபுட் 500 add பன்னு</div>
                <div class="example-item">• ட்ராவல் 1000 update பண்ணு</div>
                <div class="example-item">• கடைசி செலவு delete பண்ணு</div>
                <div class="example-item">• அனலிடிக்ஸ் show பண்ணு</div>
                <div class="example-item">• எல்லா செலவும் காட்டு</div>
                """, unsafe_allow_html=True)
    
    def render_features_showcase(self):
        """Showcase voice assistant features"""
        st.markdown("### ✨ சிறப்புக் கூறுகள் | Special Features")
        
        features = [
            {"icon": "🎯", "title": "Multi-Command", "desc": "பல கட்டளைகள் ஒரே வாக்கியத்தில்"},
            {"icon": "🗣️", "title": "Casual Tamil", "desc": "சாதாரண தமிழ் & டேங்க்ளிஷ்"},
            {"icon": "🔊", "title": "Voice Response", "desc": "தமிழில் குரல் பதில்"},
            {"icon": "🧭", "title": "Navigation", "desc": "பக்கங்களுக்கு செல்ல"},
            {"icon": "💾", "title": "CRUD Operations", "desc": "செலவுகளை சேர்/மாற்று/நீக்கு"},
            {"icon": "⚡", "title": "Real-time", "desc": "நிகழ்நேர செயலாக்கம்"}
        ]
        
        cols = st.columns(3)
        for idx, feature in enumerate(features):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon">{feature['icon']}</div>
                    <h4>{feature['title']}</h4>
                    <p>{feature['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_voice_interface(self):
        """Render main voice interface"""
        st.markdown("### 🎤 உங்கள் குருவைப் பயன்படுத்தவும் | Use Your Voice")
        
        # Status indicator
        col_status = st.columns([1, 3, 1])
        with col_status[0]:
            status_text = "✅ இணைப்பு உள்ளது" if self.check_backend_connection() else "❌ இணைப்பு இல்லை"
            st.markdown(f"**நிலை:** {status_text}")
        
        # Voice input section
        st.markdown('<div class="voice-input-section">', unsafe_allow_html=True)
        
        # Text input for manual commands
        text_command = st.text_area(
            "✍️ கட்டளையை இங்கே தட்டச்சு செய்க | Type command here:",
            placeholder="Example: Food 500 add பன்னு, Travel 300 update பண்ணு, Analytics கு போ...",
            height=100,
            key="voice_text_input"
        )
        
        col_buttons = st.columns([2, 1, 1, 1])
        
        with col_buttons[0]:
            if st.button("📤 கட்டளையை அனுப்பு | Send Command", use_container_width=True):
                if text_command:
                    self.process_text_command(text_command)
                else:
                    st.warning("தயவு செய்து ஒரு கட்டளையை உள்ளிடவும்.")
        
        with col_buttons[1]:
            # Voice recorder using file uploader
            st.markdown("#### 🎙️ பதிவு செய்க")
            audio_file = st.file_uploader(
                "ஆடியோ கோப்பை பதிவேற்று", 
                type=['wav', 'mp3', 'm4a'], 
                key="audio_uploader",
                label_visibility="collapsed"
            )
            
            if audio_file is not None:
                audio_bytes = audio_file.read()
                self.process_audio(audio_bytes)
        
        with col_buttons[2]:
            # Quick action: Add expense
            if st.button("➕ செலவு சேர்", use_container_width=True):
                self.process_text_command("Food 500 add பன்னு")
        
        with col_buttons[3]:
            # Quick action: Show analytics
            if st.button("📊 அனலிடிக்ஸ்", use_container_width=True):
                self.process_text_command("Analytics கு போ")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick commands
        st.markdown("### ⚡ விரைவு கட்டளைகள் | Quick Commands")
        
        quick_commands = {
            "➕ செலவு சேர்": "Food 500 add பன்னு",
            "🗑️ கடைசி செலவு நீக்கு": "Last expense delete பண்ணு",
            "📋 எல்லா செலவும் காட்டு": "All expenses show பண்ணு",
            "📊 அனலிடிக்ஸ் பக்கம்": "Analytics கு போ",
            "💰 பட்ஜெட் பக்கம்": "Budgets கு போ",
            "📈 டாஷ்போர்ட்": "Dashboard காட்டு"
        }
        
        cols = st.columns(3)
        for idx, (label, command) in enumerate(quick_commands.items()):
            with cols[idx % 3]:
                if st.button(label, key=f"quick_{idx}", use_container_width=True):
                    self.process_text_command(command)
    
    def render_conversation_history(self):
        """Render conversation history"""
        st.markdown("### 💬 உரையாடல் வரலாறு | Conversation History")
        
        # Initialize conversation in session state
        if 'conversation' not in st.session_state:
            st.session_state.conversation = []
        
        # Display conversation
        conversation_placeholder = st.empty()
        
        if not st.session_state.conversation:
            conversation_placeholder.info("""
            💡 உரையாடலைத் தொடங்க, குரலைப் பதிவு செய்யவும் அல்லது கட்டளையைத் தட்டச்சு செய்யவும்.
            
            **பயனுள்ள குறிப்புகள்:**
            1. தமிழ், ஆங்கிலம் அல்லது இரண்டையும் கலந்து பேசுங்கள்
            2. ஒரே வாக்கியத்தில் பல கட்டளைகளை கொடுக்கலாம்
            3. "Food 500 add பன்னு, travel 300 update பண்ணு" போல் கட்டளைகளை கொடுக்கலாம்
            4. பக்கங்களுக்கு செல்ல "Analytics கு போ" என்று சொல்லுங்கள்
            """)
        else:
            self.display_conversation(conversation_placeholder)
        
        # Clear conversation button
        col_clear = st.columns([3, 1])
        with col_clear[1]:
            if st.button("🗑️ உரையாடலை அழி | Clear Chat", use_container_width=True):
                st.session_state.conversation = []
                st.rerun()
    
    def render_assistant_analytics(self):
        """Show voice assistant analytics"""
        st.markdown("### 📊 குரல் உதவியாளர் புள்ளிவிவரங்கள் | Voice Assistant Analytics")
        
        if not st.session_state.conversation:
            st.info("இதுவரை எந்த உரையாடலும் இல்லை. | No conversations yet.")
            return
        
        # Calculate stats
        total_messages = len(st.session_state.conversation)
        user_messages = sum(1 for msg in st.session_state.conversation if msg["role"] == "user")
        assistant_messages = total_messages - user_messages
        
        # Show stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("மொத்த செய்திகள்", total_messages)
        col2.metric("உங்கள் கட்டளைகள்", user_messages)
        col3.metric("உதவியாளர் பதில்கள்", assistant_messages)
        
        # Calculate successful commands
        successful_commands = 0
        for msg in st.session_state.conversation:
            if msg["role"] == "assistant" and msg.get("actions"):
                for action in msg["actions"]:
                    if action.get("success"):
                        successful_commands += 1
        
        col4.metric("வெற்றிகரமான கட்டளைகள்", successful_commands)
        
        # Recent commands table
        st.markdown("#### 🕒 சமீபத்திய கட்டளைகள் | Recent Commands")
        recent_commands = [
            {"timestamp": msg.get("timestamp"), "command": msg["content"], "response": ""}
            for msg in st.session_state.conversation[-5:]
            if msg["role"] == "user" and msg["content"] != "🎤 பதிவு செய்யப்பட்ட குரல்..."
        ]
        
        if recent_commands:
            # Find corresponding responses
            for i, cmd in enumerate(recent_commands):
                for msg in st.session_state.conversation:
                    if msg["role"] == "assistant" and msg.get("timestamp") > cmd["timestamp"]:
                        cmd["response"] = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                        break
            
            df_recent = pd.DataFrame(recent_commands)
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("சமீபத்திய கட்டளைகள் இல்லை.")
    
    def check_backend_connection(self):
        """Check connection to backend"""
        try:
            response = requests.get(f"{self.backend_url}/voice-assistant/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def process_audio(self, audio_bytes):
        """Process audio recording"""
        try:
            # Add user message to conversation
            st.session_state.conversation.append({
                "role": "user",
                "content": "🎤 பதிவு செய்யப்பட்ட குரல்... | Recording audio...",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            audio_data_url = f"data:audio/wav;base64,{audio_base64}"
            
            # Show processing status
            with st.spinner("🔊 குரலை பகுப்பாய்வு செய்கிறது... | Analyzing voice..."):
                # Process with backend REST API
                response = requests.post(
                    f"{self.backend_url}/voice-assistant/process",
                    json={
                        "audio_data": audio_data_url,
                        "user_id": st.session_state.user_id
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add assistant response
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": result["text"],
                        "audio": result.get("audio_base64"),
                        "actions": result.get("actions", []),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Play audio response
                    if result.get("audio_base64"):
                        self.play_audio(result["audio_base64"])
                    
                    # Handle navigation
                    if result.get("navigation"):
                        st.session_state.page = result["navigation"]
                        st.success(f"✅ Navigating to {result['navigation']}")
                        time.sleep(1)
                        st.rerun()
                    
                    st.success("✅ கட்டளை செயல்படுத்தப்பட்டது! | Command executed!")
                    
                else:
                    error_msg = "❌ குரல் செயலாக்கம் தோல்வியுற்றது | Voice processing failed"
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.error(error_msg)
        
        except requests.exceptions.Timeout:
            error_msg = "⏰ கட்டமைப்பு நேரம் முடிந்தது | Request timeout"
            st.session_state.conversation.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.error(error_msg)
        except Exception as e:
            error_msg = f"❌ பிழை: {str(e)[:100]}"
            st.session_state.conversation.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.error(error_msg)
    
    def process_text_command(self, text_command):
        """Process text command"""
        try:
            if not text_command.strip():
                st.warning("தயவு செய்து ஒரு கட்டளையை உள்ளிடவும்.")
                return
            
            # Add user message to conversation
            st.session_state.conversation.append({
                "role": "user",
                "content": text_command,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            # Process with backend
            with st.spinner("🔍 கட்டளையை பகுப்பாய்வு செய்கிறது... | Analyzing command..."):
                response = requests.post(
                    f"{self.backend_url}/voice-assistant/process",
                    json={
                        "text_input": text_command,
                        "user_id": st.session_state.user_id
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add assistant response
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": result["text"],
                        "audio": result.get("audio_base64"),
                        "actions": result.get("actions", []),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Play audio response
                    if result.get("audio_base64"):
                        self.play_audio(result["audio_base64"])
                    
                    # Handle navigation
                    if result.get("navigation"):
                        st.session_state.page = result["navigation"]
                        st.success(f"✅ Navigating to {result['navigation']}")
                        time.sleep(1)
                        st.rerun()
                    
                    st.success("✅ கட்டளை செயல்படுத்தப்பட்டது! | Command executed!")
                    
                else:
                    error_msg = "❌ கட்டளை செயலாக்கம் தோல்வியுற்றது | Command processing failed"
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.error(error_msg)
        
        except requests.exceptions.Timeout:
            error_msg = "⏰ கட்டமைப்பு நேரம் முடிந்தது | Request timeout"
            st.session_state.conversation.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.error(error_msg)
        except Exception as e:
            error_msg = f"❌ பிழை: {str(e)[:100]}"
            st.session_state.conversation.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.error(error_msg)
    
    def play_audio(self, audio_base64):
        """Play base64 audio in browser"""
        try:
            if not audio_base64:
                return
                
            audio_bytes = base64.b64decode(audio_base64)
            audio_str = base64.b64encode(audio_bytes).decode()
            
            # Create HTML audio player
            audio_html = f"""
            <audio autoplay controls style="width: 100%; margin: 10px 0;">
                <source src="data:audio/mp3;base64,{audio_str}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            <script>
                document.querySelector('audio').play().catch(e => console.log('Autoplay prevented:', e));
            </script>
            """
            components.html(audio_html, height=60)
        except Exception as e:
            st.warning(f"Could not play audio: {str(e)[:50]}")
    
    def display_conversation(self, placeholder):
        """Display conversation history"""
        conversation_html = "<div class='conversation-box'>"
        
        for msg in st.session_state.conversation[-20:]:  # Show last 20 messages
            if msg["role"] == "user":
                content = msg["content"]
                if content == "🎤 பதிவு செய்யப்பட்ட குரல்... | Recording audio...":
                    content = "🎤 பதிவு செய்யப்பட்ட குரல்..."
                
                conversation_html += f"""
                <div style="text-align: right; margin: 15px 0;">
                    <div class="voice-bubble">
                        <strong>You:</strong> {content}
                        <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 5px;">{msg["timestamp"]}</div>
                    </div>
                </div>
                """
            else:
                # Assistant message with actions
                content = msg["content"]
                actions_html = ""
                
                if msg.get("actions"):
                    for action in msg["actions"]:
                        if action.get("success"):
                            icon = "✅"
                            if action.get("action") == "add":
                                actions_html += f"""
                                <div class="action-badge">
                                    {icon} ADDED: ₹{action.get('amount', '?')} to {action.get('category', 'expense')}
                                </div>
                                """
                            elif action.get("action") == "delete":
                                actions_html += f"""
                                <div class="action-badge">
                                    {icon} DELETED: {action.get('expense', 'expense')}
                                </div>
                                """
                            elif action.get("action") == "navigate":
                                actions_html += f"""
                                <div class="action-badge">
                                    {icon} NAVIGATE: to {action.get('page', 'page')}
                                </div>
                                """
                            elif action.get("action") == "read":
                                actions_html += f"""
                                <div class="action-badge">
                                    {icon} READ: {action.get('count', 0)} expenses
                                </div>
                                """
                
                conversation_html += f"""
                <div style="margin: 15px 0;">
                    <div class="assistant-bubble">
                        <strong>🤖 தமிழ் உதவியாளர்:</strong> {content}
                        <div style="margin-top: 8px;">{actions_html}</div>
                        <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 5px;">{msg["timestamp"]}</div>
                    </div>
                </div>
                """
        
        conversation_html += "</div>"
        placeholder.markdown(conversation_html, unsafe_allow_html=True)
    
    def render_test_interface(self):
        """Render test interface for voice assistant"""
        st.markdown("### 🧪 சோதனை இடைமுகம் | Test Interface")
        
        if st.button("🔍 Voice Assistant Status Check", use_container_width=True):
            try:
                response = requests.get(f"{self.backend_url}/voice-assistant/status", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ Voice Assistant Status: {data['status']}")
                    
                    # Display features
                    st.markdown("**சிறப்புக் கூறுகள்:**")
                    for feature in data.get("features", []):
                        st.write(f"• {feature}")
                    
                    # Display supported commands
                    st.markdown("**ஆதரவு தரும் கட்டளைகள்:**")
                    for cmd in data.get("supported_commands", []):
                        st.write(f"• {cmd}")
                else:
                    st.error("❌ Voice assistant not responding")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")
        
        # Test specific commands
        st.markdown("#### 🎯 கட்டளைகளை சோதிக்கவும் | Test Commands")
        test_commands = [
            "Food 500 add பன்னு",
            "Travel 1000 update பண்ணு",
            "Last expense delete பண்ணு",
            "Analytics கு போ",
            "Food 300 add, Travel 500 add, Shopping 700 add"
        ]
        
        for cmd in test_commands:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.code(cmd)
            with col2:
                if st.button("Test", key=f"test_{cmd[:10]}"):
                    self.process_text_command(cmd)

class EnhancedExpenseTracker:
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.voice_assistant = TamilVoiceAssistantUI(backend_url)
        self.setup_page()
        
    def setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="💰 Super Expense Tracker Pro with Tamil Voice Assistant",
            page_icon="🗣️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Enhanced CSS with Tamil styling
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
        
        /* Voice assistant highlight */
        .voice-highlight {
            background: linear-gradient(45deg, #FF416C, #FF4B2B);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin: 0 5px;
            animation: pulse 2s infinite;
        }
        
        /* Tamil font import */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;500;700&display=swap');
        
        .tamil-text {
            font-family: 'Noto Sans Tamil', 'Arial Unicode MS', sans-serif;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'''
        <h1 class="main-header">
            💸 Super Expense Tracker Pro 
            <span class="voice-highlight">🗣️ தமிழ் குரு உதவியாளர்</span>
        </h1>
        ''', unsafe_allow_html=True)
    
    def test_connection(self):
        """Test connection to backend"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=10)
            return response.status_code == 200
        except:
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
        if 'conversation' not in st.session_state:
            st.session_state.conversation = []
    
    def render_account_modal(self):
        """Render account creation/login modal"""
        if st.session_state.show_account_modal:
            with st.container():
                st.markdown("---")
                st.subheader("🔐 My Account")
                
                tab1, tab2, tab3, tab4 = st.tabs(["Login", "Create New Account", "Forgot Password", "Admin"])
                
                with tab1:
                    with st.form("login_form"):
                        phone_number = st.text_input("Phone Number", placeholder="Enter your phone number")
                        password = st.text_input("Password", type="password", placeholder="Enter 6-digit password")
                        login_submitted = st.form_submit_button("Login")
                        
                        if login_submitted:
                            if len(phone_number) > 0 and len(password) == 6:
                                try:
                                    response = requests.post(
                                        f"{self.backend_url}/users/login",
                                        json={"phone_number": phone_number, "password": password},
                                        timeout=10
                                    )
                                    if response.status_code == 200:
                                        data = response.json()
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.logged_in = True
                                        st.session_state.show_account_modal = False
                                        st.success("✅ Login successful!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Invalid credentials")
                                except:
                                    st.error("❌ Login failed")
                            else:
                                st.error("❌ Please enter valid phone number and 6-digit password")
                
                with tab2:
                    with st.form("register_form"):
                        new_phone = st.text_input("Phone Number", placeholder="Enter your phone number", key="new_phone")
                        new_password = st.text_input("Password", type="password", placeholder="Enter 6-digit password", key="new_password")
                        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm 6-digit password")
                        register_submitted = st.form_submit_button("Create Account")
                        
                        if register_submitted:
                            if len(new_phone) > 0 and len(new_password) == 6 and new_password == confirm_password:
                                try:
                                    response = requests.post(
                                        f"{self.backend_url}/users/register",
                                        json={"phone_number": new_phone, "password": new_password},
                                        timeout=10
                                    )
                                    if response.status_code == 200:
                                        data = response.json()
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.logged_in = True
                                        st.session_state.show_account_modal = False
                                        st.success("✅ Account created successfully!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Account creation failed")
                                except:
                                    st.error("❌ Registration failed")
                            else:
                                st.error("❌ Please check: Phone number, 6-digit password, and password confirmation")
                
                with tab3:
                    st.info("Enter admin code to reset your password")
                    with st.form("forgot_password_form"):
                        admin_code = st.text_input("Admin Code", placeholder="Enter admin code", type="password")
                        reset_phone = st.text_input("Phone Number", placeholder="Enter your phone number")
                        new_password = st.text_input("New Password", type="password", placeholder="Enter new 6-digit password")
                        reset_submitted = st.form_submit_button("Reset Password")
                        
                        if reset_submitted:
                            if admin_code and reset_phone and len(new_password) == 6:
                                try:
                                    response = requests.post(
                                        f"{self.backend_url}/users/forgot-password",
                                        json={
                                            "phone_number": reset_phone,
                                            "new_password": new_password,
                                            "admin_code": admin_code
                                        },
                                        timeout=10
                                    )
                                    if response.status_code == 200:
                                        st.success("✅ Password reset successfully!")
                                    else:
                                        st.error("❌ Password reset failed")
                                except:
                                    st.error("❌ Password reset failed")
                            else:
                                st.error("❌ Please fill all fields correctly")

                with tab4:
                    st.info("Admin access to download complete database")
                    admin_code = st.text_input("Admin Code", placeholder="Enter admin code", type="password", key="admin_code")
                    download_submitted = st.button("Download Database", key="download_db")

                    if download_submitted:
                        if admin_code == "2139":
                            try:
                                response = requests.get(
                                    f"{self.backend_url}/admin/download-db",
                                    params={"admin_code": admin_code},
                                    timeout=15
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    json_str = json.dumps(data, indent=2)
                                    st.download_button(
                                        label="📥 Download Complete Database",
                                        data=json_str,
                                        file_name=f"expense_tracker_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                        mime="application/json",
                                        key="db_download_button",
                                        use_container_width=True
                                    )
                                    st.success("✅ Database export ready for download!")
                                else:
                                    st.error("❌ Database export failed")
                            except:
                                st.error("❌ Database export failed")
                        else:
                            st.error("❌ Invalid admin code")
                
                if st.button("Close", key="close_account_modal"):
                    st.session_state.show_account_modal = False
                    st.rerun()
    
    def render_sidebar(self):
        """Render enhanced sidebar with navigation"""
        with st.sidebar:
            st.markdown("## 🧭 Navigation")
            
            # Navigation buttons with voice assistant
            pages = {
                "📊 Dashboard": "Dashboard",
                "➕ Add Expense": "Add Expense", 
                "📋 Expense List": "Expense List",
                "📈 Analytics": "Analytics",
                "💰 Budgets": "Budgets",
                "📤 Export": "Export",
                "🗣️ Tamil Voice Assistant": "Voice Assistant"
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
                    
                    # Voice assistant quick access
                    if st.button("🎤 Quick Voice Command", use_container_width=True, key="sidebar_voice"):
                        st.session_state.page = "Voice Assistant"
                        st.rerun()
            except:
                st.info("Connect to backend to see stats")
            
            st.markdown("---")
            
            # Voice assistant features showcase
            st.markdown("""
            <div style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
                        color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 1.5rem; text-align: center;">🗣️</div>
                <h4 style="text-align: center; margin: 5px 0;">Tamil Voice Assistant</h4>
                <p style="font-size: 0.9rem; text-align: center; opacity: 0.9;">
                    Speak in Tamil/English/Tanglish<br>
                    Multi-commands • Voice feedback • Navigation
                </p>
            </div>
            """, unsafe_allow_html=True)
            
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
    
    def initialize_sample_data(self):
        """Initialize sample data"""
        try:
            response = requests.post(
                f"{self.backend_url}/sample-data/initialize", 
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                st.success("✅ Sample data initialized successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize sample data")
        except:
            st.error("❌ Error initializing sample data")
    
    def get_analytics(self, start_date=None, end_date=None):
        """Get analytics from backend"""
        try:
            params = {"user_id": st.session_state.user_id}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            response = requests.get(f"{self.backend_url}/analytics/overview", params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Analytics API error: {response.status_code}")
        except:
            st.error("Error fetching analytics")
        return None
    
    def render_dashboard(self):
        """Render comprehensive dashboard"""
        st.header("📊 Financial Dashboard - INR")
        
        # Date range filter
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="dashboard_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="dashboard_end")
        with col3:
            st.write("")
            col_apply, col_clear = st.columns(2)
            with col_apply:
                if st.button("Apply Filter"):
                    st.session_state.filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
                    st.rerun()
            with col_clear:
                if st.button("Clear Filter"):
                    st.session_state.filters = {}
                    st.rerun()
        
        filter_start = st.session_state.filters.get('start_date', start_date.isoformat())
        filter_end = st.session_state.filters.get('end_date', end_date.isoformat())
        
        analytics = self.get_analytics(start_date=filter_start, end_date=filter_end)
        
        if not analytics:
            st.error("No data available for the selected period")
            return
        
        # Key Metrics
        st.subheader("📈 Key Financial Metrics")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Spent", f"{CURRENCY}{analytics.get('total_spent', 0):,.0f}")
        with col2:
            st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):.0f}")
        with col3:
            expenses = self.get_expenses(start_date=filter_start, end_date=filter_end)
            expenses_count = len(expenses)
            st.metric("Expense Count", f"{expenses_count}")
        with col4:
            categories = len(analytics.get('category_breakdown', {}))
            st.metric("Categories", f"{categories}")
        with col5:
            st.metric("Savings Rate", f"{analytics.get('savings_rate', 0):.1f}%")
        with col6:
            velocity = analytics.get('spending_velocity', {})
            change = velocity.get('change_percentage', 0)
            st.metric("Weekly Trend", f"{change:+.1f}%")
        
        # First row charts
        col1, col2 = st.columns(2)
        
        with col1:
            category_breakdown = analytics.get('category_breakdown', {})
            if category_breakdown:
                fig = px.pie(
                    values=list(category_breakdown.values()),
                    names=list(category_breakdown.keys()),
                    title="Spending by Category",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        with col2:
            monthly_trend = analytics.get('monthly_trend', [])
            if monthly_trend:
                df_trend = pd.DataFrame(monthly_trend)
                df_trend['month'] = pd.to_datetime(df_trend['month'])
                df_trend = df_trend.sort_values('month')
                fig = px.line(
                    df_trend, 
                    x='month', 
                    y='amount',
                    title="Monthly Spending Trend",
                    markers=True
                )
                fig.update_traces(line=dict(color='#1f77b4', width=3))
                fig.update_xaxes(title_text="Month")
                fig.update_yaxes(title_text=f"Amount ({CURRENCY})")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly trend data available")
        
        # Second row charts
        col1, col2 = st.columns(2)
        
        with col1:
            weekly_spending = analytics.get('weekly_spending', [])
            if weekly_spending:
                df_weekly = pd.DataFrame(weekly_spending)
                fig = px.bar(
                    df_weekly,
                    x='week',
                    y='amount',
                    title="Weekly Spending (Last 8 Weeks)",
                    color='amount',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No weekly spending data available")
        
        with col2:
            daily_pattern = analytics.get('daily_pattern', {})
            if daily_pattern:
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_data = [daily_pattern.get(day, 0) for day in days_order]
                
                fig = px.bar(
                    x=days_order,
                    y=daily_data,
                    title="Spending by Day of Week",
                    color=daily_data,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No daily pattern data available")
        
        # Top expenses table
        st.subheader("🏆 Top 10 Largest Expenses")
        top_expenses = analytics.get('top_expenses', [])
        if top_expenses:
            top_df = pd.DataFrame(top_expenses)
            if not top_df.empty:
                top_df = top_df[['date', 'description', 'category', 'amount', 'priority']]
                top_df['amount'] = top_df['amount'].apply(lambda x: f"{CURRENCY}{float(x):,.0f}")
                st.dataframe(top_df, use_container_width=True)
        else:
            st.info("No expense data available")
    
    def render_add_expense(self):
        """Render expense addition form"""
        st.header("➕ Add New Expense - INR")
        
        is_edit = st.session_state.edit_expense is not None
        expense_data = st.session_state.edit_expense or {}
        
        form_key = "edit_expense_form" if is_edit else "add_expense_form"
        
        with st.form(key=form_key):
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_input(
                    "Description *", 
                    value=expense_data.get('description', ''),
                    placeholder="e.g., Dinner at Restaurant"
                )
                amount = st.number_input(
                    f"Amount ({CURRENCY}) *", 
                    min_value=0.01, 
                    step=1.0, 
                    format="%.2f",
                    value=max(0.01, float(expense_data.get('amount', 0.0)))
                )
                category = st.selectbox(
                    "Category *",
                    options=[
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", 
                        "Travel", "Education", "Housing", "Other"
                    ],
                    index=0 if not expense_data.get('category') else [
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", 
                        "Travel", "Education", "Housing", "Other"
                    ].index(expense_data.get('category', 'Food & Dining'))
                )
            
            with col2:
                default_date = datetime.fromisoformat(expense_data.get('date')) if expense_data.get('date') else datetime.now()
                date = st.date_input("Date *", value=default_date)
                priority = st.selectbox(
                    "Priority",
                    options=["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(expense_data.get('priority', 'Medium'))
                )
                tags_default = ", ".join(expense_data.get('tags', [])) if expense_data.get('tags') else ""
                tags = st.text_input(
                    "Tags (comma separated)",
                    value=tags_default,
                    placeholder="restaurant, business, luxury"
                )
                notes = st.text_area(
                    "Notes", 
                    value=expense_data.get('notes', ''),
                    placeholder="Additional details about this expense...",
                    height=100
                )
            
            submit_text = "💾 Update Expense" if is_edit else "💾 Save Expense"
            submitted = st.form_submit_button(submit_text, use_container_width=True)
            
            if submitted:
                if not description or amount <= 0:
                    st.error("Please fill all required fields (*)")
                else:
                    expense_payload = {
                        "description": description,
                        "amount": float(amount),
                        "category": category,
                        "date": date.isoformat(),
                        "priority": priority,
                        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                        "notes": notes if notes else None
                    }
                    
                    try:
                        if is_edit:
                            response = requests.put(
                                f"{self.backend_url}/expenses/{expense_data['id']}",
                                params={"user_id": st.session_state.user_id},
                                json=expense_payload,
                                timeout=10
                            )
                            success_message = "✅ Expense updated successfully!"
                        else:
                            response = requests.post(
                                f"{self.backend_url}/expenses/",
                                params={"user_id": st.session_state.user_id},
                                json=expense_payload,
                                timeout=10
                            )
                            success_message = "✅ Expense added successfully!"
                        
                        if response.status_code == 200:
                            st.success(success_message)
                            st.balloons()
                            st.session_state.edit_expense = None
                            st.session_state.form_cleared = True
                            st.rerun()
                        else:
                            st.error("❌ Error saving expense")
                    except:
                        st.error("🚫 Failed to connect to backend")
        
        if is_edit:
            if st.button("❌ Cancel Edit", use_container_width=True):
                st.session_state.edit_expense = None
                st.rerun()
    
    def get_expenses(self, **filters):
        """Get expenses from backend"""
        try:
            params = {"user_id": st.session_state.user_id}
            
            for key, value in filters.items():
                if value is not None:
                    params[key] = value
            
            response = requests.get(f"{self.backend_url}/expenses/", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error fetching expenses: {response.status_code}")
        except:
            st.error("Error fetching expenses")
        return []
    
    def render_expense_list(self):
        """Render expense list with advanced filtering"""
        st.header("📋 Expense Management - INR")
        
        # Search bar
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "🔍 Search Expenses",
                value=st.session_state.get('search_query', ''),
                placeholder="Search by description, category, tags...",
                key="expense_search"
            )
            if search_query != st.session_state.get('search_query', ''):
                st.session_state.search_query = search_query

        with col2:
            if st.button("Clear Search", use_container_width=True):
                st.session_state.search_query = ""
                if 'filters' in st.session_state:
                    st.session_state.filters.pop('search', None)
                st.rerun()
        
        # Advanced filters
        with st.expander("🔍 Advanced Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.selectbox(
                    "Category Filter",
                    ["All"] + [
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", 
                        "Travel", "Education", "Housing", "Other"
                    ],
                    key="category_filter"
                )
                priority_filter = st.selectbox(
                    "Priority Filter", 
                    ["All", "Low", "Medium", "High"],
                    key="priority_filter"
                )
            
            with col2:
                min_amount = st.number_input(f"Min Amount ({CURRENCY})", min_value=0.0, value=0.0, step=100.0, key="min_amount")
                max_amount = st.number_input(f"Max Amount ({CURRENCY})", min_value=0.0, value=10000.0, step=100.0, key="max_amount")
            
            with col3:
                tags_filter = st.text_input("Tags Filter", placeholder="restaurant, business", key="tags_filter")
                date_range = st.selectbox(
                    "Date Range",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
                    key="date_range"
                )
            
            col_apply, col_clear = st.columns(2)
            with col_apply:
                if st.button("Apply Filters", use_container_width=True):
                    filters = {}
                    if category_filter != "All":
                        filters['category'] = category_filter
                    if priority_filter != "All":
                        filters['priority'] = priority_filter
                    if min_amount > 0:
                        filters['min_amount'] = min_amount
                    if max_amount < 10000:
                        filters['max_amount'] = max_amount
                    if tags_filter:
                        filters['tags'] = tags_filter
                    if st.session_state.search_query:
                        filters['search'] = st.session_state.search_query
                    
                    if date_range == "Last 7 Days":
                        filters['start_date'] = (datetime.now() - timedelta(days=7)).isoformat()
                    elif date_range == "Last 30 Days":
                        filters['start_date'] = (datetime.now() - timedelta(days=30)).isoformat()
                    elif date_range == "Last 90 Days":
                        filters['start_date'] = (datetime.now() - timedelta(days=90)).isoformat()
                    
                    st.session_state.filters = filters
                    st.rerun()
            with col_clear:
                if st.button("Clear All Filters", use_container_width=True):
                    st.session_state.filters = {}
                    st.session_state.search_query = ""
                    st.rerun()
        
        filters = st.session_state.get('filters', {}).copy()
        if st.session_state.search_query:
            filters['search'] = st.session_state.search_query
        
        expenses = self.get_expenses(**filters)
        
        if not expenses:
            st.info("No expenses found matching your filters.")
            return
        
        df = pd.DataFrame(expenses)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['amount'] = df['amount'].round(2)
        
        # Summary
        st.subheader(f"📊 Summary ({len(expenses)} expenses)")
        total_amount = df['amount'].sum() if not df.empty else 0
        avg_amount = df['amount'].mean() if not df.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", f"{CURRENCY}{total_amount:,.0f}")
        col2.metric("Average", f"{CURRENCY}{avg_amount:.0f}")
        col3.metric("Largest", f"{CURRENCY}{df['amount'].max():.0f}" if not df.empty else f"{CURRENCY}0")
        col4.metric("Smallest", f"{CURRENCY}{df['amount'].min():.0f}" if not df.empty else f"{CURRENCY}0")
        
        # Expense display
        st.subheader("💳 Expense Details (Newest First)")
        
        for expense in expenses:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{expense['date']}**")
                with col2:
                    st.write(f"**{expense['description']}**")
                    if expense.get('notes'):
                        st.caption(f"📝 {expense['notes']}")
                    if expense.get('tags'):
                        tags = expense['tags']
                        if isinstance(tags, str):
                            tags = [tags]
                        tags_str = " ".join([f"🏷️{tag}" for tag in tags])
                        st.caption(tags_str)
                with col3:
                    st.write(f"`{expense['category']}`")
                with col4:
                    priority_color = {
                        "High": "red", 
                        "Medium": "orange", 
                        "Low": "green"
                    }
                    priority = expense.get('priority', 'Medium')
                    st.write(f":{priority_color.get(priority, 'orange')}[**{priority}**]")
                with col5:
                    st.write(f"**{CURRENCY}{float(expense['amount']):.0f}**")
                    
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{expense['id']}"):
                            st.session_state.edit_expense = expense
                            st.session_state.page = "Add Expense"
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{expense['id']}"):
                            self.delete_expense(expense['id'])
                
                st.markdown("---")
    
    def delete_expense(self, expense_id):
        """Delete an expense"""
        try:
            response = requests.delete(
                f"{self.backend_url}/expenses/{expense_id}", 
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                st.success("✅ Expense deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete expense")
        except:
            st.error("❌ Error deleting expense")
    
    def render_analytics(self):
        """Render comprehensive analytics page"""
        st.header("📈 Advanced Analytics - INR")
        
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox(
                "Analysis Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time"]
            )
        
        end_date = datetime.now()
        if period == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif period == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif period == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        elif period == "Last Year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime(2020, 1, 1)
        
        analytics = self.get_analytics(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        if not analytics:
            st.info("No data available for analytics")
            return
        
        st.subheader("📊 Comprehensive Financial Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Analysis Period", f"{CURRENCY}{analytics.get('total_spent', 0):,.0f}")
        with col2:
            st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):.0f}")
        with col3:
            st.metric("Savings Rate", f"{analytics.get('savings_rate', 0):.1f}%")
        with col4:
            velocity = analytics.get('spending_velocity', {})
            change = velocity.get('change_percentage', 0)
            st.metric("Spending Trend", f"{change:+.1f}%")
        
        st.subheader("📈 Comparative Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            daily_pattern = analytics.get('daily_pattern', {})
            if daily_pattern:
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                daily_data = [daily_pattern.get(day, 0) for day in days_order]
                
                fig = px.bar(
                    x=days_order,
                    y=daily_data,
                    title="Average Spending by Day of Week",
                    color=daily_data,
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No daily pattern data available")
        
        with col2:
            category_breakdown = analytics.get('category_breakdown', {})
            if category_breakdown:
                categories = list(category_breakdown.keys())
                amounts = list(category_breakdown.values())
                
                fig = px.pie(
                    values=amounts,
                    names=categories,
                    title="Category Distribution",
                    hole=0.3
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        st.subheader("🔍 Deep Dive Analytics")
        col1, col2 = st.columns(2)
        
        with col1:
            spending_velocity = analytics.get('spending_velocity', {})
            if spending_velocity:
                current = spending_velocity.get('current_week', 0)
                previous = spending_velocity.get('previous_week', 0)
                
                fig = px.bar(
                    x=['Current Week', 'Previous Week'],
                    y=[current, previous],
                    title="Weekly Spending Comparison",
                    color=[current, previous],
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending velocity data available")
        
        with col2:
            priority_distribution = analytics.get('priority_distribution', {})
            if priority_distribution:
                fig = px.pie(
                    values=list(priority_distribution.values()),
                    names=list(priority_distribution.keys()),
                    title="Spending by Priority Level",
                    color=list(priority_distribution.keys()),
                    color_discrete_map={
                        'High': '#ff4b4b',
                        'Medium': '#ffa500', 
                        'Low': '#4b8aff'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No priority distribution data available")
        
        st.subheader("🏥 Financial Health Score")
        
        savings_rate = analytics.get('savings_rate', 0)
        health_score = min(100, max(0, savings_rate + 50))
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = health_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Financial Health Score"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ]
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_budgets(self):
        """Render budget management page"""
        st.header("💰 Budget Management & Alerts - INR")
        
        try:
            response = requests.get(
                f"{self.backend_url}/budgets/alerts", 
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                alerts = response.json()
                
                if not alerts:
                    st.success("🎉 All budgets are within limits!")
                else:
                    st.subheader("⚠️ Budget Alerts")
                    
                    for alert in alerts:
                        if alert['alert_level'] == "Critical":
                            st.markdown(f'<div class="alert-critical">🚨 CRITICAL: {alert["category"]} - {CURRENCY}{alert["spent"]:.0f} / {CURRENCY}{alert["budget"]:.0f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
                        elif alert['alert_level'] == "Warning":
                            st.markdown(f'<div class="alert-warning">⚠️ WARNING: {alert["category"]} - {CURRENCY}{alert["spent"]:.0f} / {CURRENCY}{alert["budget"]:.0f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="alert-info">ℹ️ INFO: {alert["category"]} - {CURRENCY}{alert["spent"]:.0f} / {CURRENCY}{alert["budget"]:.0f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
            else:
                st.info("No budget alerts data available")
        
        except:
            st.error("Error loading budget alerts")
        
        st.subheader("🎯 Set Custom Budgets")
        st.info("Configure your monthly budget limits for each category:")
        
        categories = [
            "Food & Dining", "Transportation", "Entertainment", 
            "Utilities", "Shopping", "Healthcare", 
            "Travel", "Education", "Housing", "Other"
        ]
        
        try:
            response = requests.get(f"{self.backend_url}/budgets/{st.session_state.user_id}", timeout=10)
            if response.status_code == 200:
                user_budgets = response.json()
            else:
                user_budgets = {}
        except:
            user_budgets = {}
        
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
        
        cols = st.columns(2)
        budget_values = {}
        for i, category in enumerate(categories):
            with cols[i % 2]:
                default_value = user_budgets.get(category, default_budgets.get(category, 5000))
                budget_values[category] = st.number_input(
                    f"{category} Budget ({CURRENCY})",
                    min_value=0.0,
                    value=float(default_value),
                    step=500.0,
                    key=f"budget_{category}"
                )
        
        if st.button("💾 Save Budgets", use_container_width=True):
            try:
                response = requests.post(
                    f"{self.backend_url}/budgets/{st.session_state.user_id}",
                    json=budget_values,
                    timeout=10
                )
                if response.status_code == 200:
                    st.success("✅ Budget limits saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to save budgets")
            except:
                st.error("❌ Error saving budgets")
    
    def render_export(self):
        """Render data export page"""
        st.header("📤 Data Export & Reports - INR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export Options")
            export_format = st.selectbox("Format", ["JSON", "CSV"])
            
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="export_start")
            end_date = st.date_input("End Date", datetime.now(), key="export_end")
            
            if st.button("📥 Generate Export", use_container_width=True):
                try:
                    response = requests.get(
                        f"{self.backend_url}/reports/export",
                        params={
                            "user_id": st.session_state.user_id,
                            "format": export_format.lower(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat()
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if export_format == "CSV":
                            csv_data = data['csv']
                            st.download_button(
                                label="📋 Download CSV",
                                data=csv_data,
                                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            json_str = json.dumps(data, indent=2)
                            st.download_button(
                                label="📄 Download JSON",
                                data=json_str,
                                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        st.success("✅ Export generated successfully!")
                    else:
                        st.error("❌ Failed to generate export")
                    
                except:
                    st.error("❌ Error generating export")
        
        with col2:
            st.subheader("Quick Reports")
            
            report_type = st.selectbox(
                "Report Type",
                ["Spending Summary", "Category Analysis", "Monthly Report", "Budget vs Actual"]
            )
            
            if st.button("📊 Generate Report", use_container_width=True):
                try:
                    expenses = self.get_expenses()
                    if expenses:
                        df = pd.DataFrame(expenses)
                        
                        if report_type == "Spending Summary":
                            st.subheader("📋 Spending Summary Report")
                            summary = df.groupby('category')['amount'].agg(['sum', 'count', 'mean']).reset_index()
                            summary.columns = ['Category', 'Total Amount', 'Number of Expenses', 'Average Amount']
                            summary['Total Amount'] = summary['Total Amount'].apply(lambda x: f"{CURRENCY}{float(x):,.0f}")
                            summary['Average Amount'] = summary['Average Amount'].apply(lambda x: f"{CURRENCY}{float(x):,.0f}")
                            st.dataframe(summary, use_container_width=True)
                            
                        elif report_type == "Category Analysis":
                            st.subheader("📊 Category Analysis Report")
                            df['amount'] = df['amount'].astype(float)
                            category_stats = df.groupby('category').agg({
                                'amount': ['sum', 'count', 'mean', 'max']
                            }).round(2)
                            category_stats.columns = ['Total', 'Count', 'Average', 'Max']
                            st.dataframe(category_stats, use_container_width=True)
                            
                        elif report_type == "Monthly Report":
                            st.subheader("📅 Monthly Report")
                            df['date'] = pd.to_datetime(df['date'])
                            df['month'] = df['date'].dt.to_period('M')
                            df['amount'] = df['amount'].astype(float)
                            monthly = df.groupby('month').agg({
                                'amount': ['sum', 'count'],
                                'category': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'N/A'
                            }).round(2)
                            monthly.columns = ['Total Amount', 'Expense Count', 'Most Common Category']
                            st.dataframe(monthly, use_container_width=True)
                            
                        elif report_type == "Budget vs Actual":
                            st.subheader("💰 Budget vs Actual Report")
                            try:
                                response = requests.get(
                                    f"{self.backend_url}/budgets/alerts", 
                                    params={"user_id": st.session_state.user_id},
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    budget_alerts = response.json()
                                    if budget_alerts:
                                        budget_df = pd.DataFrame(budget_alerts)
                                        budget_df = budget_df[['category', 'spent', 'budget', 'percentage']]
                                        budget_df['spent'] = budget_df['spent'].apply(lambda x: f"{CURRENCY}{x:.0f}")
                                        budget_df['budget'] = budget_df['budget'].apply(lambda x: f"{CURRENCY}{x:.0f}")
                                        budget_df['percentage'] = budget_df['percentage'].apply(lambda x: f"{x:.1f}%")
                                        st.dataframe(budget_df, use_container_width=True)
                                    else:
                                        st.info("No budget data available for comparison")
                                else:
                                    st.info("No budget data available for comparison")
                            except:
                                st.info("Budget comparison data not available")
                    
                    else:
                        st.warning("No expenses data available for report generation")
                        
                except Exception as e:
                    st.error(f"❌ Error generating report: {e}")
    
    def render_voice_assistant_page(self):
        """Render the Tamil Voice Assistant page"""
        self.voice_assistant.render_header()
        self.voice_assistant.render_features_showcase()
        self.voice_assistant.render_command_examples()
        self.voice_assistant.render_voice_interface()
        self.voice_assistant.render_conversation_history()
        self.voice_assistant.render_assistant_analytics()
        
        # Test interface
        with st.expander("🧪 சோதனை இடைமுகம் | Test Interface", expanded=False):
            self.voice_assistant.render_test_interface()
    
    def render_footer(self):
        """Render footer with tech stack"""
        st.markdown("""
        <div class="footer">
            <p><strong>Tech Stack:</strong> FastAPI • Streamlit • Plotly • Pandas • Tamil Voice Assistant</p>
            <p><strong>Voice Features:</strong> Groq Whisper • gTTS • Tamil/English/Tanglish • Multi-Command</p>
            <p>© 2024 Expense Tracker Pro with Tamil Voice Assistant. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main method to run the application"""
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
            self.render_voice_assistant_page()
        
        # Render footer
        self.render_footer()

# Run the application
if __name__ == "__main__":
    app = EnhancedExpenseTracker(BACKEND_URL)
    app.run()
