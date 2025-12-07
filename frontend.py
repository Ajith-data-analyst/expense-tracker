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
import wave
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")
CURRENCY = "₹"

class EnhancedExpenseTracker:
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.setup_page()

    def setup_page(self):
        """Configure Streamlit page settings with enhanced styling"""
        st.set_page_config(
            page_title="💰 Super Expense Tracker Pro - INR",
            page_icon="💸",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.markdown("""
        <style>
            :root {
                --primary-color: #FF6B6B;
                --secondary-color: #4ECDC4;
                --accent-color: #FFE66D;
                --bg-light: #F7F9FB;
                --text-dark: #2C3E50;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            
            .main {
                background: var(--bg-light);
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            h1, h2, h3 {
                color: var(--text-dark);
                font-weight: 600;
                margin-bottom: 15px;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                text-align: center;
            }
            
            .stButton>button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .expense-item {
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                border-left: 4px solid var(--secondary-color);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .sidebar-nav {
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .success-message {
                background: #D4EDDA;
                color: #155724;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #28A745;
            }
            
            .error-message {
                background: #F8D7DA;
                color: #721C24;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                border-left: 4px solid #F5C6CB;
            }
        </style>
        """, unsafe_allow_html=True)

    def setup_session_state(self):
        """Initialize session state variables"""
        if "page" not in st.session_state:
            st.session_state.page = "Dashboard"
        if "user_id" not in st.session_state:
            st.session_state.user_id = "default"
        if "transcription" not in st.session_state:
            st.session_state.transcription = ""
        if "voice_result" not in st.session_state:
            st.session_state.voice_result = None

    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("### 📱 Navigation")
            
            pages = [
                ("🏠 Dashboard", "Dashboard"),
                ("➕ Add Expense", "Add Expense"),
                ("📊 Analytics", "Analytics"),
                ("📋 View All", "View All"),
                ("💼 Budget Manager", "Budget Manager"),
                ("⚙️ Settings", "Settings"),
                ("🗣️ Voice Assistant", "Voice Assistant"),
            ]
            
            for label, page_name in pages:
                if st.button(label, use_container_width=True, 
                           key=f"nav_{page_name}",
                           type="primary" if st.session_state.page == page_name else "secondary"):
                    st.session_state.page = page_name
                    st.rerun()

    def fetch_expenses(self):
        """Fetch expenses from backend"""
        try:
            response = requests.get(
                f"{self.backend_url}/expenses/",
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch expenses: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching expenses: {str(e)}")
            return []

    def fetch_analytics(self):
        """Fetch analytics from backend"""
        try:
            response = requests.get(
                f"{self.backend_url}/analytics/overview",
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch analytics: {response.status_code}")
                return {}
        except Exception as e:
            st.error(f"Error fetching analytics: {str(e)}")
            return {}

    def render_dashboard(self):
        """Render dashboard page"""
        st.markdown("# 🏠 Dashboard")
        
        expenses = self.fetch_expenses()
        analytics = self.fetch_analytics()
        
        if not expenses:
            st.info("📭 No expenses recorded yet. Add your first expense!")
            return

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Spent</h3>
                <h1>{CURRENCY}{analytics.get('total_spent', 0):,.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Daily Average</h3>
                <h1>{CURRENCY}{analytics.get('average_daily', 0):,.2f}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Top Category</h3>
                <h1>{list(analytics.get('category_breakdown', {}).keys())[0] if analytics.get('category_breakdown') else 'N/A'}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Savings Rate</h3>
                <h1>{analytics.get('savings_rate', 0):.1f}%</h1>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Category breakdown
        category_data = analytics.get('category_breakdown', {})
        if category_data:
            fig = px.pie(
                values=list(category_data.values()),
                names=list(category_data.keys()),
                title="💰 Spending by Category",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent expenses
        st.markdown("### 📌 Recent Expenses")
        recent_expenses = sorted(expenses, key=lambda x: x.get('date', ''), reverse=True)[:5]
        
        for exp in recent_expenses:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"**{exp.get('description', 'N/A')}**")
            with col2:
                st.write(f"{exp.get('category', 'N/A')}")
            with col3:
                st.write(f"{CURRENCY}{exp.get('amount', 0)}")
            with col4:
                st.write(f"{exp.get('date', 'N/A')}")

    def render_add_expense(self):
        """Render add expense page"""
        st.markdown("# ➕ Add New Expense")
        
        with st.form("add_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_input("Description", placeholder="e.g., Coffee at Cafe")
                amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0)
            
            with col2:
                category = st.selectbox(
                    "Category",
                    ["Food & Dining", "Transportation", "Entertainment", "Education", 
                     "Utilities", "Housing", "Healthcare", "Other"]
                )
                date = st.date_input("Date", datetime.now())
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            with col2:
                tags = st.multiselect("Tags", ["work", "personal", "travel", "shopping", "food"])
            
            notes = st.text_area("Notes (optional)", height=80)
            
            if st.form_submit_button("✅ Add Expense", use_container_width=True):
                try:
                    payload = {
                        "description": description,
                        "amount": amount,
                        "category": category,
                        "date": date.isoformat(),
                        "priority": priority,
                        "tags": tags,
                        "notes": notes
                    }
                    
                    response = requests.post(
                        f"{self.backend_url}/expenses/",
                        json=payload,
                        params={"user_id": st.session_state.user_id},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Expense added successfully!")
                        st.balloons()
                    else:
                        st.error(f"Failed to add expense: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def render_analytics(self):
        """Render analytics page"""
        st.markdown("# 📊 Analytics & Insights")
        
        analytics = self.fetch_analytics()
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spent", f"{CURRENCY}{analytics.get('total_spent', 0):,.2f}")
        with col2:
            st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):,.2f}")
        with col3:
            st.metric("Savings Rate", f"{analytics.get('savings_rate', 0):.1f}%")

        st.markdown("---")

        col1, col2 = st.columns(2)
        
        # Monthly trend
        with col1:
            monthly_data = analytics.get('monthly_trend', [])
            if monthly_data:
                fig = px.bar(
                    x=[m['month'] for m in monthly_data],
                    y=[m['amount'] for m in monthly_data],
                    title="📈 Monthly Spending Trend",
                    labels={'x': 'Month', 'y': 'Amount (₹)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Weekly spending
        with col2:
            weekly_data = analytics.get('weekly_spending', [])
            if weekly_data:
                fig = px.line(
                    x=[w['week'] for w in weekly_data],
                    y=[w['amount'] for w in weekly_data],
                    title="📉 Weekly Spending Pattern",
                    labels={'x': 'Week', 'y': 'Amount (₹)'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        
        # Priority distribution
        with col1:
            priority_data = analytics.get('priority_distribution', {})
            if priority_data:
                fig = px.pie(
                    values=list(priority_data.values()),
                    names=list(priority_data.keys()),
                    title="🎯 Spending by Priority"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top expenses
        with col2:
            top_expenses = analytics.get('top_expenses', [])
            if top_expenses:
                fig = px.bar(
                    x=[e['description'] for e in top_expenses],
                    y=[e['amount'] for e in top_expenses],
                    title="💸 Top Expenses",
                    labels={'x': 'Description', 'y': 'Amount (₹)'}
                )
                st.plotly_chart(fig, use_container_width=True)

    def render_view_all(self):
        """Render view all expenses page"""
        st.markdown("# 📋 All Expenses")
        
        expenses = self.fetch_expenses()
        
        if not expenses:
            st.info("No expenses found")
            return

        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = ["All"] + list(set([e.get('category', 'Other') for e in expenses]))
            selected_category = st.selectbox("Category", categories)
        
        with col2:
            priorities = ["All"] + list(set([e.get('priority', 'Medium') for e in expenses]))
            selected_priority = st.selectbox("Priority", priorities)
        
        with col3:
            min_amount = st.number_input("Min Amount", min_value=0.0, step=100.0)

        # Apply filters
        filtered = expenses
        if selected_category != "All":
            filtered = [e for e in filtered if e.get('category') == selected_category]
        if selected_priority != "All":
            filtered = [e for e in filtered if e.get('priority') == selected_priority]
        filtered = [e for e in filtered if float(e.get('amount', 0)) >= min_amount]

        # Display table
        if filtered:
            df = pd.DataFrame(filtered)
            df['amount'] = df['amount'].apply(lambda x: f"{CURRENCY}{x:,.2f}")
            st.dataframe(df[['description', 'category', 'amount', 'priority', 'date']], use_container_width=True)
        else:
            st.info("No expenses match the selected filters")

    def render_budget_manager(self):
        """Render budget manager page"""
        st.markdown("# 💼 Budget Manager")
        
        categories = ["Food & Dining", "Transportation", "Entertainment", "Education", 
                     "Utilities", "Housing", "Healthcare", "Other"]
        
        st.markdown("### 📊 Set Monthly Budgets")
        
        budgets = {}
        cols = st.columns(2)
        for i, category in enumerate(categories):
            with cols[i % 2]:
                budgets[category] = st.number_input(
                    f"{category} Budget (₹)",
                    min_value=0.0,
                    step=500.0,
                    key=f"budget_{category}"
                )
        
        if st.button("💾 Save Budgets", use_container_width=True):
            try:
                response = requests.post(
                    f"{self.backend_url}/budgets/",
                    json=budgets,
                    params={"user_id": st.session_state.user_id},
                    timeout=10
                )
                if response.status_code == 200:
                    st.success("✅ Budgets saved successfully!")
                else:
                    st.error(f"Failed to save budgets: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    def render_settings(self):
        """Render settings page"""
        st.markdown("# ⚙️ Settings")
        
        st.markdown("### 👤 User Information")
        st.text_input("User ID", st.session_state.user_id, disabled=True)
        
        st.markdown("### 🎨 Preferences")
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        
        st.markdown("### 📦 Data Management")
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        if st.button("🗑️ Clear Local Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")

    def render_voice_assistant(self):
        """Render voice assistant page"""
        st.markdown("# 🗣️ Voice Assistant")
        
        st.info("🎙️ **Voice Assistant**: Speak in Tamil/Tanglish to manage your expenses. Example: 'Food 200 add பண்ணு'")
        
        # WebRTC configuration
        rtc_configuration = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        
        webrtc_ctx = webrtc_streamer(
            key="expense-voice-assistant",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={"audio": True, "video": False},
            async_processing=True,
        )

        if webrtc_ctx.state.playing:
            st.info("🔴 Recording... Speak now!")
            
            # Collect audio frames
            audio_frames = []
            
            try:
                while webrtc_ctx.state.playing:
                    if webrtc_ctx.audio_processor:
                        audio_data = webrtc_ctx.audio_processor.frames
                        if audio_data:
                            for frame in audio_data:
                                if frame.format.sample_rate == 16000:
                                    audio_frames.append(frame.to_ndarray().flatten())
            except Exception as e:
                st.warning(f"Recording note: {str(e)}")

            if audio_frames:
                # Combine audio frames
                audio_data = np.concatenate(audio_frames).astype(np.int16)
                
                # Save as WAV in memory
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data.tobytes())
                
                wav_buffer.seek(0)
                audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
                
                # Send to backend
                try:
                    response = requests.post(
                        f"{self.backend_url}/voice/execute-actions",
                        json={"transcription": ""},  # Backend will call transcribe first
                        files={"audio": ("audio.wav", audio_base64)},
                        params={"user_id": st.session_state.user_id},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.voice_result = result
                        st.success("✅ Voice command processed!")
                    else:
                        st.error(f"Failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        # Display results
        if st.session_state.voice_result:
            result = st.session_state.voice_result
            
            st.markdown("### 📝 Transcription")
            st.info(f"**{result.get('transcription', 'N/A')}**")
            
            st.markdown("### ✅ Actions Performed")
            actions = result.get('actions', [])
            for action in actions:
                status_emoji = "✅" if action.get('status') == 'success' else "❌"
                st.write(f"{status_emoji} {action.get('summary', 'Unknown action')}")
            
            st.markdown("### 🗨️ Confirmations")
            confirmations = result.get('confirmations', [])
            for conf in confirmations:
                st.success(conf)
            
            # Play TTS audio
            if result.get('tts_base64'):
                st.markdown("### 🔊 Audio Confirmation")
                audio_bytes = base64.b64decode(result['tts_base64'])
                st.audio(audio_bytes, format='audio/mp3')
            
            # Navigation
            if result.get('navigation'):
                nav_target = result.get('navigation')
                st.markdown(f"### 🧭 Navigating to {nav_target}...")
                st.session_state.page = nav_target
                st.rerun()

    def run(self):
        """Main app runner"""
        self.setup_session_state()
        self.render_sidebar()
        
        # Route to correct page
        if st.session_state.page == "Dashboard":
            self.render_dashboard()
        elif st.session_state.page == "Add Expense":
            self.render_add_expense()
        elif st.session_state.page == "Analytics":
            self.render_analytics()
        elif st.session_state.page == "View All":
            self.render_view_all()
        elif st.session_state.page == "Budget Manager":
            self.render_budget_manager()
        elif st.session_state.page == "Settings":
            self.render_settings()
        elif st.session_state.page == "Voice Assistant":
            self.render_voice_assistant()

if __name__ == "__main__":
    app = EnhancedExpenseTracker(BACKEND_URL)
    app.run()
