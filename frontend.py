import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import base64
import os
import json

# Page configuration
st.set_page_config(
    page_title="Expense Tracker with Voice Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = "default"
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_expenses():
    """Fetch all expenses"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/expenses/",
            params={"user_id": st.session_state.user_id}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching expenses: {e}")
        return []

def create_expense(description, amount, category, date, priority, tags, notes):
    """Create new expense"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/expenses/",
            json={
                "description": description,
                "amount": float(amount),
                "category": category,
                "date": date,
                "priority": priority,
                "tags": tags,
                "notes": notes
            },
            params={"user_id": st.session_state.user_id}
        )
        if response.status_code == 200:
            st.success("Expense added successfully!")
            return True
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def delete_expense(expense_id):
    """Delete an expense"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/expenses/{expense_id}",
            params={"user_id": st.session_state.user_id}
        )
        if response.status_code == 200:
            st.success("Expense deleted!")
            return True
        else:
            st.error("Error deleting expense")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def get_analytics():
    """Fetch analytics"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/analytics/overview",
            params={"user_id": st.session_state.user_id}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")
        return None

def get_budget_alerts():
    """Fetch budget alerts"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/budgets/alerts",
            params={"user_id": st.session_state.user_id}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []

def get_user_budgets():
    """Fetch user budgets"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/budgets/{st.session_state.user_id}"
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        return {}

def save_budgets(budgets):
    """Save user budgets"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/budgets/{st.session_state.user_id}",
            json=budgets
        )
        if response.status_code == 200:
            st.success("Budgets saved!")
            return True
        else:
            st.error("Error saving budgets")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

def dashboard_page():
    st.title("📊 Dashboard")
    st.markdown("---")
    
    analytics = get_analytics()
    if not analytics:
        st.info("No expenses yet. Add some expenses to see analytics!")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Spent", f"₹{analytics['total_spent']:.2f}")
    with col2:
        st.metric("Daily Average", f"₹{analytics['average_daily']:.2f}")
    with col3:
        st.metric("Savings Rate", f"{analytics['savings_rate']:.1f}%")
    with col4:
        alerts = get_budget_alerts()
        st.metric("Budget Alerts", len(alerts))
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Category breakdown
        if analytics['category_breakdown']:
            fig = px.pie(
                values=list(analytics['category_breakdown'].values()),
                names=list(analytics['category_breakdown'].keys()),
                title="Spending by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Monthly trend
        if analytics['monthly_trend']:
            df = pd.DataFrame(analytics['monthly_trend'])
            fig = px.line(df, x='month', y='amount', title="Monthly Spending Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    # Weekly spending
    if analytics['weekly_spending']:
        df = pd.DataFrame(analytics['weekly_spending'])
        fig = px.bar(df, x='week', y='amount', title="Weekly Spending")
        st.plotly_chart(fig, use_container_width=True)
    
    # Budget alerts
    if get_budget_alerts():
        st.subheader("⚠️ Budget Alerts")
        alerts = get_budget_alerts()
        for alert in alerts:
            color = "red" if alert['alert_level'] == "Critical" else "orange" if alert['alert_level'] == "Warning" else "blue"
            st.markdown(f"**:{color}[{alert['category']}]** - {alert['percentage']:.1f}% of budget (₹{alert['spent']:.2f} / ₹{alert['budget']:.2f})")

# ============================================================================
# PAGE: ADD EXPENSE
# ============================================================================

def add_expense_page():
    st.title("➕ Add Expense")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        description = st.text_input("Description", placeholder="e.g., Lunch at restaurant")
        category = st.selectbox(
            "Category",
            ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Utilities", "Education", "Healthcare", "Housing", "Other"]
        )
        date = st.date_input("Date", datetime.now())
    
    with col2:
        amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0)
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        tags = st.multiselect("Tags", ["food", "travel", "shopping", "entertainment", "study", "other"])
    
    notes = st.text_area("Notes", placeholder="Add any additional notes", height=100)
    
    if st.button("💾 Add Expense", use_container_width=True, type="primary"):
        if description and amount > 0:
            if create_expense(description, amount, category, date.isoformat(), priority, tags, notes):
                st.rerun()
        else:
            st.error("Please enter description and amount")

# ============================================================================
# PAGE: VIEW ALL
# ============================================================================

def view_all_page():
    st.title("📋 View All Expenses")
    st.markdown("---")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.multiselect(
            "Category",
            ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Utilities", "Education", "Healthcare", "Housing", "Other"],
            default=[]
        )
    
    with col2:
        priority_filter = st.multiselect("Priority", ["Low", "Medium", "High"], default=[])
    
    with col3:
        min_amount = st.number_input("Min Amount (₹)", min_value=0.0, value=0.0)
    
    with col4:
        max_amount = st.number_input("Max Amount (₹)", min_value=0.0, value=100000.0)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Get expenses
    expenses = get_expenses()
    
    # Apply filters
    filtered = expenses
    if category_filter:
        filtered = [e for e in filtered if e['category'] in category_filter]
    if priority_filter:
        filtered = [e for e in filtered if e['priority'] in priority_filter]
    filtered = [e for e in filtered if min_amount <= float(e['amount']) <= max_amount]
    filtered = [e for e in filtered if e['date'] >= start_date.isoformat() and e['date'] <= end_date.isoformat()]
    
    # Display table
    if filtered:
        df = pd.DataFrame(filtered)
        df = df[['date', 'category', 'description', 'amount', 'priority', 'tags']]
        df['amount'] = df['amount'].apply(lambda x: f"₹{x:.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Delete option
        st.subheader("Delete Expense")
        expense_to_delete = st.selectbox(
            "Select expense to delete",
            [f"{e['date']} - {e['category']} - ₹{e['amount']}" for e in filtered],
            key="delete_select"
        )
        
        if st.button("🗑️ Delete", type="secondary"):
            idx = [f"{e['date']} - {e['category']} - ₹{e['amount']}" for e in filtered].index(expense_to_delete)
            if delete_expense(filtered[idx]['id']):
                st.rerun()
    else:
        st.info("No expenses found matching the filters")

# ============================================================================
# PAGE: ANALYTICS
# ============================================================================

def analytics_page():
    st.title("📈 Analytics")
    st.markdown("---")
    
    analytics = get_analytics()
    if not analytics:
        st.info("No data available for analytics")
        return
    
    # Summary
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Spent", f"₹{analytics['total_spent']:.2f}")
    with col2:
        st.metric("Avg Daily", f"₹{analytics['average_daily']:.2f}")
    with col3:
        st.metric("Savings Rate", f"{analytics['savings_rate']:.1f}%")
    with col4:
        if analytics['spending_velocity']['previous_week'] > 0:
            change = analytics['spending_velocity']['change_percentage']
            st.metric("Week Change", f"{change:.1f}%")
    with col5:
        st.metric("Top Expense", f"₹{max([e['amount'] for e in analytics['top_expenses']], default=0):.2f}")
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        if analytics['category_breakdown']:
            fig = px.pie(
                values=list(analytics['category_breakdown'].values()),
                names=list(analytics['category_breakdown'].keys()),
                title="Spending Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if analytics['priority_distribution']:
            fig = px.bar(
                x=list(analytics['priority_distribution'].keys()),
                y=list(analytics['priority_distribution'].values()),
                title="Spending by Priority",
                labels={'x': 'Priority', 'y': 'Amount (₹)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if analytics['monthly_trend']:
            df = pd.DataFrame(analytics['monthly_trend'])
            fig = px.line(df, x='month', y='amount', title="Monthly Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if analytics['daily_pattern']:
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily = {k: v for k, v in analytics['daily_pattern'].items() if k in days_order}
            daily = {k: daily.get(k, 0) for k in days_order}
            fig = px.bar(
                x=list(daily.keys()),
                y=list(daily.values()),
                title="Spending by Day of Week",
                labels={'x': 'Day', 'y': 'Amount (₹)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Top expenses
    if analytics['top_expenses']:
        st.subheader("💸 Top 10 Expenses")
        top_df = pd.DataFrame(analytics['top_expenses'][:10])
        top_df = top_df[['date', 'category', 'description', 'amount']]
        top_df['amount'] = top_df['amount'].apply(lambda x: f"₹{x:.2f}")
        st.dataframe(top_df, use_container_width=True, hide_index=True)

# ============================================================================
# PAGE: BUDGET MANAGER
# ============================================================================

def budget_manager_page():
    st.title("💰 Budget Manager")
    st.markdown("---")
    
    # Get current budgets
    budgets = get_user_budgets()
    default_budgets = {
        "Food & Dining": 6000, "Transportation": 2000, "Entertainment": 1500,
        "Utilities": 1500, "Shopping": 2000, "Healthcare": 1000,
        "Travel": 3000, "Education": 3000, "Housing": 8000, "Other": 2000
    }
    
    all_budgets = {**default_budgets, **budgets}
    
    # Edit budgets
    st.subheader("Edit Monthly Budgets")
    edited_budgets = {}
    
    cols = st.columns(3)
    for idx, (category, default_amount) in enumerate(all_budgets.items()):
        with cols[idx % 3]:
            edited_budgets[category] = st.number_input(
                category,
                value=float(default_amount),
                min_value=0.0,
                step=100.0,
                key=f"budget_{category}"
            )
    
    if st.button("💾 Save Budgets", use_container_width=True, type="primary"):
        if save_budgets(edited_budgets):
            st.rerun()
    
    st.markdown("---")
    
    # Show alerts
    alerts = get_budget_alerts()
    if alerts:
        st.subheader("⚠️ Budget Status")
        for alert in alerts:
            if alert['alert_level'] == 'Critical':
                st.error(f"🔴 **{alert['category']}**: {alert['percentage']:.1f}% - ₹{alert['spent']:.2f} / ₹{alert['budget']:.2f}")
            elif alert['alert_level'] == 'Warning':
                st.warning(f"🟡 **{alert['category']}**: {alert['percentage']:.1f}% - ₹{alert['spent']:.2f} / ₹{alert['budget']:.2f}")
            else:
                st.info(f"🔵 **{alert['category']}**: {alert['percentage']:.1f}% - ₹{alert['spent']:.2f} / ₹{alert['budget']:.2f}")
    else:
        st.success("✅ All budgets are on track!")

# ============================================================================
# PAGE: VOICE ASSISTANT
# ============================================================================

def voice_assistant_page():
    st.title("🗣️ Voice Assistant")
    st.markdown("---")
    
    with st.expander("📖 How to Use Voice Commands", expanded=True):
        st.markdown("""
        **🎤 Voice Command Examples:**
        
        **Add Expense:**
        - "Food 200 add பண்ணு" → Adds ₹200 to Food & Dining
        - "travel 150 add செய்" → Adds ₹150 to Transportation
        
        **Update Expense:**
        - "travel 150 update பண்ணு" → Updates Transportation to ₹150
        
        **Delete Expense:**
        - "last entry delete" → Deletes most recent expense
        
        **Navigate:**
        - "analytics கு போ" → Goes to Analytics
        - "dashboard" → Opens Dashboard
        - "list காட்டு" → Shows all expenses
        
        **Supported Categories:**
        Food, Travel, Shopping, Entertainment, Education, Utilities, Healthcare, Housing
        
        **Languages:** Tamil (தமிழ்), Tanglish (English + Tamil mix)
        """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎤 Enter Voice Command")
        voice_input = st.text_input(
            "Enter your voice command (Tamil/Tanglish):",
            placeholder="e.g., Food 200 add பண்ணு",
            key="voice_command_input"
        )
        
        if st.button("🎙️ Execute Command", use_container_width=True, type="primary"):
            if voice_input:
                with st.spinner("Processing command..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/voice/execute-actions",
                            json={
                                "transcription": voice_input,
                                "user_id": st.session_state.user_id
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Display transcription
                            st.subheader("📝 Transcription:")
                            st.write(f"**{result['transcription']}**")
                            
                            # Display actions
                            if result.get('actions'):
                                st.subheader("✅ Actions Executed:")
                                for action in result['actions']:
                                    status_emoji = "✅" if action['status'] == "success" else "❌" if action['status'] == "failed" else "⏳"
                                    st.write(f"{status_emoji} **{action['type'].upper()}**: {action['summary']}")
                            
                            # Display confirmations
                            if result.get('confirmations'):
                                st.subheader("🔊 Tamil Confirmations:")
                                for confirmation in result['confirmations']:
                                    st.info(confirmation)
                            
                            # Play audio if available
                            if result.get('tts_audio_base64'):
                                try:
                                    st.subheader("🔊 Audio Confirmation:")
                                    audio_bytes = base64.b64decode(result['tts_audio_base64'])
                                    st.audio(audio_bytes, format='audio/wav')
                                except:
                                    pass
                            
                            # Handle navigation
                            if result.get('navigation'):
                                st.success(f"🧭 Navigating to {result['navigation']}...")
                                st.session_state.page = result['navigation']
                                st.rerun()
                        else:
                            st.error(f"Error: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error executing command: {str(e)}")
            else:
                st.warning("Please enter a command")
    
    with col2:
        st.subheader("📊 Status")
        st.markdown("""
        **Status:** ✅ Active
        
        **Features:**
        - 🎤 Speech Input
        - 🗣️ Tamil Recognition
        - 📝 Multi-action
        - ✏️ CRUD Ops
        - 🔊 TTS Audio
        - 🧭 Navigation
        
        **API:** Groq Whisper
        """)

# ============================================================================
# PAGE: SETTINGS
# ============================================================================

def settings_page():
    st.title("⚙️ Settings")
    st.markdown("---")
    
    st.subheader("Account Information")
    st.write(f"**User ID:** `{st.session_state.user_id}`")
    st.write(f"**Backend URL:** `{BACKEND_URL}`")
    
    st.markdown("---")
    
    st.subheader("🗑️ Danger Zone")
    if st.button("Clear All Data (Requires Confirmation)", type="secondary"):
        st.warning("This action cannot be undone!")
        if st.button("Yes, delete all data", type="primary"):
            st.info("Feature coming soon")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Sidebar
    with st.sidebar:
        st.title("💰 Expense Tracker")
        st.markdown("---")
        
        # Navigation
        st.subheader("📍 Navigation")
        pages = ["📊 Dashboard", "➕ Add Expense", "📋 View All", "📈 Analytics", "💰 Budget Manager", "🗣️ Voice Assistant", "⚙️ Settings"]
        selected_page = st.radio("Go to:", pages, label_visibility="collapsed")
        
        st.markdown("---")
        
        # Quick Stats
        expenses = get_expenses()
        if expenses:
            total = sum(float(e['amount']) for e in expenses)
            st.metric("Total Expenses", f"₹{total:.2f}")
            st.metric("Total Records", len(expenses))
        
        st.markdown("---")
        st.caption("v3.0.0 with Voice Assistant")
    
    # Route to pages
    if selected_page == "📊 Dashboard":
        dashboard_page()
    elif selected_page == "➕ Add Expense":
        add_expense_page()
    elif selected_page == "📋 View All":
        view_all_page()
    elif selected_page == "📈 Analytics":
        analytics_page()
    elif selected_page == "💰 Budget Manager":
        budget_manager_page()
    elif selected_page == "🗣️ Voice Assistant":
        voice_assistant_page()
    elif selected_page == "⚙️ Settings":
        settings_page()

if __name__ == "__main__":
    main()
