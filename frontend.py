import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from streamlit_mic_recorder import mic_recorder

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")
CURRENCY = "₹"  # Indian Rupee

class VoiceAssistant:
    """Voice Assistant for Expense Tracker with Audio Intake"""
    def __init__(self, backend_url):
        self.backend_url = backend_url
    
    def process_command(self, command: str, user_id: str = "default") -> dict:
        """Process voice command via backend"""
        try:
            response = requests.post(
                f"{self.backend_url}/voice/process",
                json={"command": command, "user_id": user_id},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Voice processing error: {str(e)}",
                "action": "error"
            }
    
    def transcribe_audio(self, audio_bytes, user_id: str = "default") -> dict:
        """Transcribe audio file to text"""
        try:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            response = requests.post(
                f"{self.backend_url}/voice/transcribe",
                files=files,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Audio transcription error: {str(e)}"
            }
    
    def get_commands_help(self) -> dict:
        """Get available voice commands"""
        try:
            response = requests.get(
                f"{self.backend_url}/voice/commands",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}

class EnhancedExpenseTracker:
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.voice_assistant = VoiceAssistant(backend_url)
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page settings with enhanced styling"""
        st.set_page_config(
            page_title="💰 Super Expense Tracker Pro - INR",
            page_icon="💸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for enhanced styling and responsiveness
        st.markdown("""
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .main {
                background-color: #f8f9fa;
            }
            
            .stApp {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            
            .title-text {
                color: #2d3748;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 2.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .metric-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin: 10px 0;
                border-left: 5px solid #667eea;
            }
            
            .expense-item {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 8px 0;
                border-left: 4px solid #667eea;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .budget-alert {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #f56565;
            }
            
            .success-message {
                background: #c6f6d5;
                color: #22543d;
                padding: 12px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #48bb78;
            }
            
            .error-message {
                background: #fed7d7;
                color: #742a2a;
                padding: 12px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #f56565;
            }
            
            .voice-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .voice-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 12px rgba(102, 126, 234, 0.4);
            }
            
            .voice-button:active {
                transform: translateY(0);
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<h1 class="title-text">💰 Enhanced Expense Tracker Pro with Voice Audio</h1>', unsafe_allow_html=True)
    
    def get_user_id(self) -> str:
        """Get current user ID"""
        return st.session_state.get("user_id", "default")
    
    def show_voice_assistant_widget(self):
        """Display voice assistant widget with audio intake"""
        st.subheader("🎤 Voice Assistant Control Panel")
        
        # Tabs for different input methods
        tab1, tab2, tab3 = st.tabs(["🎙️ Voice Input", "📝 Text Input", "❓ Help"])
        
        with tab1:
            st.info("🎙️ Click the microphone button below to record your voice command")
            
            # Voice recording using streamlit-mic-recorder
            audio = mic_recorder(
                start_prompt="🎙️ Click to Start Recording",
                stop_prompt="⏹️ Click to Stop Recording",
                just_once=False,
                use_container_width=True,
                format="wav"
            )
            
            if audio:
                st.success("✅ Audio recorded successfully!")
                
                with st.spinner("Transcribing audio..."):
                    # Transcribe audio
                    transcription_result = self.voice_assistant.transcribe_audio(audio["bytes"], self.get_user_id())
                    
                    if transcription_result.get("status") == "success":
                        transcribed_text = transcription_result.get("transcribed_text", "")
                        st.markdown(f'<div class="success-message">📝 Transcribed: "{transcribed_text}"</div>', unsafe_allow_html=True)
                        
                        # Process the transcribed text
                        with st.spinner("Processing command..."):
                            result = self.voice_assistant.process_command(transcribed_text, self.get_user_id())
                            
                            if result.get("status") == "success":
                                st.markdown(f'<div class="success-message">✅ {result.get("message", "")}</div>', unsafe_allow_html=True)
                                
                                # Handle navigation
                                if result.get("action") in ["navigate_home", "navigate_analytics", "navigate_budgets", "navigate_expenses"]:
                                    if "analytics" in result.get("action").lower():
                                        st.session_state.page = "analytics"
                                    elif "budget" in result.get("action").lower():
                                        st.session_state.page = "budgets"
                                    elif "expense" in result.get("action").lower():
                                        st.session_state.page = "expenses"
                                    else:
                                        st.session_state.page = "home"
                                    st.rerun()
                                
                                # Display data if available
                                if result.get("data"):
                                    with st.expander("📊 Result Details"):
                                        st.json(result.get("data"))
                            else:
                                st.markdown(f'<div class="error-message">❌ {result.get("message", "Unknown error")}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-message">❌ {transcription_result.get("message", "Transcription failed")}</div>', unsafe_allow_html=True)
        
        with tab2:
            st.info("📝 Type your voice command below")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                voice_input = st.text_input(
                    "🗣️ Enter your command:",
                    placeholder="e.g., 'Add 500 for food' or 'Show my expenses'",
                    key="voice_command_input"
                )
            
            with col2:
                submit_voice = st.button("📤 Process Command", key="submit_voice")
            
            with col3:
                show_help = st.button("❓ Show Help", key="show_voice_help")
            
            # Process voice command
            if submit_voice and voice_input:
                with st.spinner("Processing command..."):
                    result = self.voice_assistant.process_command(voice_input, self.get_user_id())
                    
                    if result.get("status") == "success":
                        st.markdown(f'<div class="success-message">✅ {result.get("message", "")}</div>', unsafe_allow_html=True)
                        
                        # Handle navigation
                        if result.get("action") in ["navigate_home", "navigate_analytics", "navigate_budgets", "navigate_expenses"]:
                            if "analytics" in result.get("action").lower():
                                st.session_state.page = "analytics"
                            elif "budget" in result.get("action").lower():
                                st.session_state.page = "budgets"
                            elif "expense" in result.get("action").lower():
                                st.session_state.page = "expenses"
                            else:
                                st.session_state.page = "home"
                            st.rerun()
                        
                        # Display data if available
                        if result.get("data"):
                            with st.expander("📊 Result Details"):
                                st.json(result.get("data"))
                    else:
                        st.markdown(f'<div class="error-message">❌ {result.get("message", "Unknown error")}</div>', unsafe_allow_html=True)
            
            if show_help:
                st.info("Displaying help...")
        
        with tab3:
            with st.expander("📚 Available Voice Commands", expanded=True):
                st.markdown("""
                ### 📝 Add Expenses
                - "Add 500 for food"
                - "Create expense of 1000 in education"
                - "Log 250 rupees for transport"
                
                ### 📊 View Data
                - "Show my expenses"
                - "Show total spent"
                - "Show analytics"
                - "Display budget alerts"
                
                ### 🔍 Filter & Search
                - "Show food expenses"
                - "Filter by entertainment"
                - "Transportation spending"
                
                ### 🧭 Navigate
                - "Go to analytics"
                - "Open expenses"
                - "Navigate to budgets"
                - "Show home"
                
                ### ℹ️ Help
                - "Help"
                - "What can you do"
                - "Available commands"
                """)
    
    def create_expense_manual(self):
        """Manual expense creation form"""
        st.subheader("➕ Add New Expense (Manual)")
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_input("Expense Description", placeholder="e.g., Lunch at cafe")
                amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0)
            
            with col2:
                category = st.selectbox(
                    "Category",
                    ["Food & Dining", "Transportation", "Entertainment", "Education", "Housing",
                     "Utilities", "Shopping", "Healthcare", "Travel", "Other"]
                )
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            tags_input = st.text_input("Tags (comma-separated)", placeholder="e.g., restaurant, lunch")
            notes = st.text_area("Notes", placeholder="Additional details")
            
            submit_button = st.form_submit_button("💾 Save Expense", use_container_width=True)
            
            if submit_button:
                if not description or amount <= 0:
                    st.error("Please fill in all required fields correctly")
                else:
                    try:
                        expense_data = {
                            "description": description,
                            "amount": float(amount),
                            "category": category,
                            "date": datetime.now().date().isoformat(),
                            "priority": priority,
                            "tags": [tag.strip() for tag in tags_input.split(",") if tag.strip()],
                            "notes": notes if notes else None
                        }
                        
                        response = requests.post(
                            f"{self.backend_url}/expenses/?user_id={self.get_user_id()}",
                            json=expense_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            st.markdown(
                                f'<div class="success-message">✅ Expense added successfully! ₹{amount} for {category}</div>',
                                unsafe_allow_html=True
                            )
                            st.rerun()
                        else:
                            st.error(f"Failed to add expense: {response.text}")
                    except Exception as e:
                        st.error(f"Error adding expense: {str(e)}")
    
    def manage_expenses(self):
        """Manage expenses page"""
        st.subheader("📝 Manage Expenses")
        
        try:
            response = requests.get(
                f"{self.backend_url}/expenses/?user_id={self.get_user_id()}",
                timeout=10
            )
            
            if response.status_code == 200:
                expenses = response.json()
                
                # Add manual form
                self.create_expense_manual()
                
                st.divider()
                
                if expenses:
                    st.info(f"Total expenses: {len(expenses)}")
                    
                    # Filter options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        filter_category = st.selectbox(
                            "Filter by Category",
                            ["All"] + list(set(e["category"] for e in expenses))
                        )
                    with col2:
                        filter_priority = st.selectbox(
                            "Filter by Priority",
                            ["All", "High", "Medium", "Low"]
                        )
                    with col3:
                        search_term = st.text_input("Search in description/tags")
                    
                    # Apply filters
                    filtered = expenses
                    if filter_category != "All":
                        filtered = [e for e in filtered if e["category"] == filter_category]
                    if filter_priority != "All":
                        filtered = [e for e in filtered if e["priority"] == filter_priority]
                    if search_term:
                        filtered = [e for e in filtered if search_term.lower() in e["description"].lower()]
                    
                    # Display expenses
                    for exp in filtered:
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        with col1:
                            st.write(f"**{exp['description']}** - {exp['category']}")
                        with col2:
                            st.write(f"₹{exp['amount']:.2f}")
                        with col3:
                            st.write(f"🔴 {exp['priority']}")
                        with col4:
                            if st.button("🗑️", key=f"delete_{exp['id']}", help="Delete expense"):
                                self.delete_expense(exp["id"])
                else:
                    st.info("No expenses found")
            else:
                st.error("Failed to fetch expenses")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def delete_expense(self, expense_id: str):
        """Delete an expense"""
        try:
            response = requests.delete(
                f"{self.backend_url}/expenses/{expense_id}?user_id={self.get_user_id()}",
                timeout=10
            )
            if response.status_code == 200:
                st.success("Expense deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete expense")
        except Exception as e:
            st.error(f"Error deleting expense: {str(e)}")
    
    def show_analytics_page(self):
        """Show advanced analytics"""
        st.subheader("📊 Advanced Analytics")
        
        try:
            response = requests.get(
                f"{self.backend_url}/analytics/?user_id={self.get_user_id()}",
                timeout=10
            )
            
            if response.status_code == 200:
                analytics = response.json()
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Spent", f"₹{analytics['total_spent']:.2f}")
                with col2:
                    st.metric("Daily Average", f"₹{analytics['average_daily']:.2f}")
                with col3:
                    st.metric("Savings Rate", f"{analytics['savings_rate']:.1f}%")
                with col4:
                    st.metric("Spending Change", f"{analytics['spending_velocity']['change_percentage']:.1f}%")
                
                st.divider()
                
                # Category breakdown
                if analytics["category_breakdown"]:
                    st.subheading("💰 Category Breakdown")
                    fig = px.pie(
                        values=list(analytics["category_breakdown"].values()),
                        names=list(analytics["category_breakdown"].keys()),
                        title="Spending by Category"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Monthly trend
                if analytics["monthly_trend"]:
                    st.subheading("📈 Monthly Spending Trend")
                    monthly_df = pd.DataFrame(analytics["monthly_trend"])
                    fig = px.line(monthly_df, x="month", y="total", markers=True, title="Monthly Spending")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Priority distribution
                if analytics["priority_distribution"]:
                    st.subheading("🎯 Priority Distribution")
                    priority_df = pd.DataFrame([
                        {"Priority": k, "Amount": v}
                        for k, v in analytics["priority_distribution"].items()
                    ])
                    fig = px.bar(priority_df, x="Priority", y="Amount", title="Spending by Priority")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to fetch analytics")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def show_budgets_page(self):
        """Show budget alerts"""
        st.subheader("💳 Budget Alerts & Monitoring")
        
        try:
            response = requests.get(
                f"{self.backend_url}/budgets/alerts?user_id={self.get_user_id()}",
                timeout=10
            )
            
            if response.status_code == 200:
                alerts = response.json()
                
                if alerts:
                    for alert in alerts:
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{alert['category']}**")
                        with col2:
                            st.write(f"₹{alert['spent']:.2f} / ₹{alert['budget']:.2f}")
                        with col3:
                            progress = alert["percentage"] / 100
                            st.progress(progress)
                        with col4:
                            if alert["alert_level"] == "Critical":
                                st.error(f"🔴 {alert['alert_level']}")
                            elif alert["alert_level"] == "Warning":
                                st.warning(f"🟠 {alert['alert_level']}")
                            else:
                                st.success(f"🟢 {alert['alert_level']}")
                else:
                    st.info("No budget alerts")
            else:
                st.error("Failed to fetch budget alerts")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def main(self):
        """Main application"""
        # Initialize session state
        if "page" not in st.session_state:
            st.session_state.page = "home"
        if "user_id" not in st.session_state:
            st.session_state.user_id = "default"
        
        # Sidebar
        with st.sidebar:
            st.title("🧭 Navigation")
            
            # User ID input
            user_id = st.text_input("User ID", value=st.session_state.user_id)
            if user_id:
                st.session_state.user_id = user_id
            
            # Navigation
            page = st.radio(
                "Select Page",
                ["🏠 Home", "📝 Manage Expenses", "📊 Analytics", "💳 Budget Alerts", "🎤 Voice Commands"],
                key="page_radio"
            )
            
            if page == "🏠 Home":
                st.session_state.page = "home"
            elif page == "📝 Manage Expenses":
                st.session_state.page = "expenses"
            elif page == "📊 Analytics":
                st.session_state.page = "analytics"
            elif page == "💳 Budget Alerts":
                st.session_state.page = "budgets"
            elif page == "🎤 Voice Commands":
                st.session_state.page = "voice"
        
        # Main content
        if st.session_state.page == "home":
            st.markdown("---")
            st.markdown("### 📊 Welcome to Enhanced Expense Tracker Pro with Voice Audio")
            st.info("🎤 Use voice commands (speak or type) or manual input to track your expenses. Navigate using the sidebar or voice assistant.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Add Expense", use_container_width=True):
                    st.session_state.page = "expenses"
                    st.rerun()
            with col2:
                if st.button("📊 View Analytics", use_container_width=True):
                    st.session_state.page = "analytics"
                    st.rerun()
            
            self.show_voice_assistant_widget()
        
        elif st.session_state.page == "expenses":
            self.manage_expenses()
        
        elif st.session_state.page == "analytics":
            self.show_analytics_page()
        
        elif st.session_state.page == "budgets":
            self.show_budgets_page()
        
        elif st.session_state.page == "voice":
            st.subheader("🎤 Voice Assistant with Audio Intake")
            self.show_voice_assistant_widget()

def main():
    tracker = EnhancedExpenseTracker(BACKEND_URL)
    tracker.main()

if __name__ == "__main__":
    main()
