import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import time
import base64

# Configuration - Use environment variable for backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
CURRENCY = "₹"  # Indian Rupee

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
        
        # Custom CSS for enhanced styling and responsiveness
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            h1, h2, h3 {
                color: #1e3a8a;
                font-weight: 700;
            }
            .stMetric {
                background-color: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .stButton>button {
                width: 100%;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = "Dashboard"
        if 'user_id' not in st.session_state:
            st.session_state.user_id = "default"
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'show_account_modal' not in st.session_state:
            st.session_state.show_account_modal = False
        if 'show_forgot_password' not in st.session_state:
            st.session_state.show_forgot_password = False
        if 'show_reset_password' not in st.session_state:
            st.session_state.show_reset_password = False
        if 'show_export_modal' not in st.session_state:
            st.session_state.show_export_modal = False
        if 'reset_phone' not in st.session_state:
            st.session_state.reset_phone = ""
        if 'loading' not in st.session_state:
            st.session_state.loading = False
        if 'filters' not in st.session_state:
            st.session_state.filters = {}
        if 'edit_expense' not in st.session_state:
            st.session_state.edit_expense = None
    
    def set_loading(self, state):
        """Set loading state"""
        st.session_state.loading = state
    
    def show_toast(self, message, type="info"):
        """Show toast notification"""
        if type == "success":
            st.success(message)
        elif type == "error":
            st.error(message)
        elif type == "warning":
            st.warning(message)
        else:
            st.info(message)
    
    def render_loading_spinner(self):
        """Render loading spinner"""
        st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div class="spinner"></div>
                <p>Loading... Please wait</p>
            </div>
        """, unsafe_allow_html=True)
    
    def render_forgot_password_modal(self):
        """Render forgot password modal"""
        if st.session_state.show_forgot_password:
            with st.container():
                st.markdown("---")
                st.subheader("🔑 Forgot Password")
                with st.form("forgot_password_form"):
                    phone_number = st.text_input("Phone Number", placeholder="Enter your registered phone number")
                    submit_forgot = st.form_submit_button("Send Reset Code")
                    
                    if submit_forgot:
                        if len(phone_number) > 0:
                            try:
                                self.set_loading(True)
                                response = requests.post(
                                    f"{self.backend_url}/users/forgot-password",
                                    json={"phone_number": phone_number}
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    st.session_state.reset_phone = phone_number
                                    st.session_state.show_forgot_password = False
                                    st.session_state.show_reset_password = True
                                    self.show_toast("✅ Reset code sent successfully!", "success")
                                    st.rerun()
                                else:
                                    self.show_toast("❌ Phone number not found", "error")
                            except Exception as e:
                                self.show_toast(f"❌ Error: {e}", "error")
                            finally:
                                self.set_loading(False)
                        else:
                            self.show_toast("❌ Please enter your phone number", "error")
                
                if st.button("Back to Login"):
                    st.session_state.show_forgot_password = False
                    st.rerun()
    
    def render_reset_password_modal(self):
        """Render reset password modal"""
        if st.session_state.show_reset_password:
            with st.container():
                st.markdown("---")
                st.subheader("🔄 Reset Password")
                with st.form("reset_password_form"):
                    st.info(f"Reset code sent to: {st.session_state.reset_phone}")
                    reset_code = st.text_input("Reset Code", placeholder="Enter 6-digit code")
                    new_password = st.text_input("New Password", type="password", placeholder="Enter new 6-digit password")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm new password")
                    submit_reset = st.form_submit_button("Reset Password")
                    
                    if submit_reset:
                        if (len(reset_code) == 6 and len(new_password) == 6 and new_password == confirm_password):
                            try:
                                self.set_loading(True)
                                response = requests.post(
                                    f"{self.backend_url}/users/reset-password",
                                    json={
                                        "phone_number": st.session_state.reset_phone,
                                        "reset_code": reset_code,
                                        "new_password": new_password
                                    }
                                )
                                if response.status_code == 200:
                                    st.session_state.show_reset_password = False
                                    self.show_toast("✅ Password reset successfully!", "success")
                                    st.rerun()
                                else:
                                    error_detail = response.json().get('detail', 'Invalid code')
                                    self.show_toast(f"❌ {error_detail}", "error")
                            except Exception as e:
                                self.show_toast(f"❌ Error: {e}", "error")
                            finally:
                                self.set_loading(False)
                        else:
                            self.show_toast("❌ Please check: 6-digit code and matching passwords", "error")
                
                if st.button("Back"):
                    st.session_state.show_reset_password = False
                    st.session_state.show_forgot_password = True
                    st.rerun()
    
    def render_export_modal(self):
        """Render export database modal"""
        if st.session_state.show_export_modal:
            with st.container():
                st.markdown("---")
                st.subheader("💾 Export All Data")
                st.warning("⚠️ This will download ALL your data including expenses, budgets, and profile.")
                with st.form("export_form"):
                    password = st.text_input("Export Password", type="password", placeholder="Enter export password '2139'")
                    submit_export = st.form_submit_button("📥 Download All Data")
                    
                    if submit_export:
                        if password == "2139":
                            try:
                                self.set_loading(True)
                                response = requests.post(
                                    f"{self.backend_url}/users/{st.session_state.user_id}/export-all-data",
                                    json={"password": password}
                                )
                                if response.status_code == 200:
                                    # Create download button
                                    zip_content = response.content
                                    st.download_button(
                                        label="💾 Click to Download ZIP",
                                        data=zip_content,
                                        file_name=f"expense_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                        mime="application/zip",
                                        use_container_width=True
                                    )
                                    self.show_toast("✅ Data exported successfully!", "success")
                                else:
                                    self.show_toast("❌ Export failed", "error")
                            except Exception as e:
                                self.show_toast(f"❌ Export error: {e}", "error")
                            finally:
                                self.set_loading(False)
                        else:
                            self.show_toast("❌ Invalid export password", "error")
                
                if st.button("Close Export"):
                    st.session_state.show_export_modal = False
                    st.rerun()
    
    def render_account_modal(self):
        """Render account creation/login modal"""
        if st.session_state.show_account_modal:
            with st.container():
                st.markdown("---")
                st.subheader("🔐 My Account")
                
                tab1, tab2 = st.tabs(["Login", "Create New Account"])
                
                with tab1:
                    with st.form("login_form"):
                        phone_number = st.text_input("Phone Number", placeholder="Enter your phone number")
                        password = st.text_input("Password", type="password", placeholder="Enter 6-digit password")
                        col1, col2 = st.columns(2)
                        with col1:
                            login_submitted = st.form_submit_button("Login")
                        with col2:
                            forgot_password = st.form_submit_button("Forgot Password?")
                        
                        if login_submitted:
                            if len(phone_number) > 0 and len(password) == 6:
                                try:
                                    self.set_loading(True)
                                    response = requests.post(
                                        f"{self.backend_url}/users/login",
                                        json={"phone_number": phone_number, "password": password}
                                    )
                                    if response.status_code == 200:
                                        data = response.json()
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.logged_in = True
                                        st.session_state.show_account_modal = False
                                        self.show_toast("✅ Login successful!", "success")
                                        st.rerun()
                                    else:
                                        self.show_toast("❌ Invalid credentials", "error")
                                except Exception as e:
                                    self.show_toast(f"❌ Login failed: {e}", "error")
                                finally:
                                    self.set_loading(False)
                            else:
                                self.show_toast("❌ Please enter valid phone number and 6-digit password", "error")
                        
                        if forgot_password:
                            st.session_state.show_forgot_password = True
                            st.rerun()
                
                with tab2:
                    with st.form("register_form"):
                        new_phone = st.text_input("Phone Number", placeholder="Enter your phone number", key="new_phone")
                        new_password = st.text_input("Password", type="password", placeholder="Enter 6-digit password", key="new_password")
                        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm 6-digit password")
                        register_submitted = st.form_submit_button("Create Account")
                        
                        if register_submitted:
                            if len(new_phone) > 0 and len(new_password) == 6 and new_password == confirm_password:
                                try:
                                    self.set_loading(True)
                                    response = requests.post(
                                        f"{self.backend_url}/users/register",
                                        json={"phone_number": new_phone, "password": new_password}
                                    )
                                    if response.status_code == 200:
                                        data = response.json()
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.logged_in = True
                                        st.session_state.show_account_modal = False
                                        self.show_toast("✅ Account created successfully!", "success")
                                        st.rerun()
                                    else:
                                        error_detail = response.json().get('detail', 'Registration failed')
                                        self.show_toast(f"❌ {error_detail}", "error")
                                except Exception as e:
                                    self.show_toast(f"❌ Registration failed: {e}", "error")
                                finally:
                                    self.set_loading(False)
                            else:
                                self.show_toast("❌ Please check: Phone number, 6-digit password, and password confirmation", "error")
                
                if st.button("Close"):
                    st.session_state.show_account_modal = False
                    st.rerun()
        
        # Render sub-modals
        self.render_forgot_password_modal()
        self.render_reset_password_modal()
        self.render_export_modal()
        
        # Show loading spinner if loading
        if st.session_state.loading:
            self.render_loading_spinner()
    
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
                "📤 Export": "Export"
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
            
            # Account management
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👤 My Account", use_container_width=True):
                    st.session_state.show_account_modal = True
                    st.rerun()
            with col2:
                if st.button("💾 Export DB", use_container_width=True):
                    st.session_state.show_export_modal = True
                    st.rerun()
            
            if st.session_state.logged_in and st.session_state.user_id != "default":
                st.info(f"🔐 Logged in as: {st.session_state.user_id[:8]}...")
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.logged_in = False
                    st.session_state.user_id = "default"
                    self.show_toast("✅ Logged out successfully", "success")
                    st.rerun()
    
    def initialize_sample_data(self):
        """Initialize sample data"""
        try:
            self.set_loading(True)
            response = requests.post(f"{self.backend_url}/sample-data/initialize", 
                                   params={"user_id": st.session_state.user_id})
            if response.status_code == 200:
                self.show_toast("✅ Sample data initialized successfully!", "success")
                st.rerun()
            else:
                self.show_toast("❌ Failed to initialize sample data", "error")
        except Exception as e:
            self.show_toast(f"❌ Error initializing sample data: {e}", "error")
        finally:
            self.set_loading(False)
    
    def get_analytics(self, start_date=None, end_date=None):
        """Get analytics from backend"""
        try:
            self.set_loading(True)
            params = {"user_id": st.session_state.user_id}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = requests.get(f"{self.backend_url}/analytics/overview", 
                                  params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.show_toast(f"Error fetching analytics: {e}", "error")
        finally:
            self.set_loading(False)
        return None
    
    def render_dashboard(self):
        """Render comprehensive dashboard"""
        st.header("📊 Financial Dashboard - INR")
        
        # Quick date range presets
        st.subheader("⏰ Quick Date Range")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("Today", use_container_width=True):
                today = datetime.now().date()
                st.session_state.filters = {'start_date': today.isoformat(), 'end_date': today.isoformat()}
                self.show_toast("📅 Filter applied: Today", "info")
                st.rerun()
        
        with col2:
            if st.button("7 Days", use_container_width=True):
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
                st.session_state.filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
                self.show_toast("📅 Filter applied: Last 7 Days", "info")
                st.rerun()
        
        with col3:
            if st.button("30 Days", use_container_width=True):
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
                st.session_state.filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
                self.show_toast("📅 Filter applied: Last 30 Days", "info")
                st.rerun()
        
        with col4:
            if st.button("90 Days", use_container_width=True):
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=90)
                st.session_state.filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
                self.show_toast("📅 Filter applied: Last 90 Days", "info")
                st.rerun()
        
        with col5:
            if st.button("All Time", use_container_width=True):
                st.session_state.filters = {}
                self.show_toast("📅 Filter applied: All Time", "info")
                st.rerun()
        
        # Date range filter with clear option
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
                    self.show_toast("✅ Custom filter applied", "success")
            with col_clear:
                if st.button("Clear Filter"):
                    st.session_state.filters = {}
                    self.show_toast("🧹 Filters cleared", "info")
                    st.rerun()
        
        analytics = self.get_analytics(
            start_date=st.session_state.filters.get('start_date', start_date.isoformat()),
            end_date=st.session_state.filters.get('end_date', end_date.isoformat())
        )
        
        if not analytics:
            st.error("No data available for the selected period")
            return
        
        # Enhanced Key Metrics - Fixed expense count
        st.subheader("📈 Key Financial Metrics")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("Total Spent", f"{CURRENCY}{analytics.get('total_spent', 0):,.0f}")
        with col2:
            st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):.0f}")
        with col3:
            # Fixed: Get actual expense count from filtered data
            expenses_count = len(self.get_expenses(
                start_date=st.session_state.filters.get('start_date'),
                end_date=st.session_state.filters.get('end_date')
            ))
            st.metric("Expense Count", f"{expenses_count}")
        with col4:
            categories = len(analytics.get('category_breakdown', {}))
            st.metric("Categories", f"{categories}")
        with col5:
            savings_rate = analytics.get('savings_rate', 0)
            savings_icon = "📈" if savings_rate > 20 else "📉" if savings_rate < 10 else "➡️"
            st.metric("Savings Rate", f"{savings_rate:.1f}% {savings_icon}")
        with col6:
            velocity = analytics.get('spending_velocity', {})
            change = velocity.get('change_percentage', 0)
            trend_icon = "📈" if change < 0 else "📉" if change > 0 else "➡️"
            st.metric("Weekly Trend", f"{change:+.1f}% {trend_icon}")
        
        # First row charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Category breakdown pie chart
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
            # Monthly trend - Fixed
            monthly_trend = analytics.get('monthly_trend', [])
            if monthly_trend:
                df_trend = pd.DataFrame(monthly_trend)
                # Sort by month to ensure proper ordering
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
            # Weekly spending
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
            # Daily pattern
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
        """Render enhanced expense addition form - COMPLETELY FIXED VERSION"""
        st.header("➕ Add New Expense - INR")
        
        # Check if we're in edit mode
        is_edit = st.session_state.edit_expense is not None
        expense_data = st.session_state.edit_expense or {}
        
        # Create a simple form without complex parameters that might cause issues
        form_key = "edit_expense_form" if is_edit else "add_expense_form"
        
        with st.form(key=form_key):
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_input(
                    "Description *",
                    value=expense_data.get('description', ''),
                    placeholder="e.g., Dinner at Restaurant",
                    help="Enter a clear description of the expense"
                )
                
                amount = st.number_input(
                    f"Amount ({CURRENCY}) *",
                    min_value=0.01,
                    step=1.0,
                    format="%.2f",
                    value=float(expense_data.get('amount', 0.0)),
                    help="Enter the expense amount"
                )
                
                category = st.selectbox(
                    "Category *",
                    options=[
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", "Travel", 
                        "Education", "Housing", "Other"
                    ],
                    index=0 if not expense_data.get('category') else [
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", "Travel", 
                        "Education", "Housing", "Other"
                    ].index(expense_data.get('category', 'Food & Dining'))
                )
            
            with col2:
                default_date = datetime.fromisoformat(expense_data.get('date')) if expense_data.get('date') else datetime.now()
                date = st.date_input("Date *", value=default_date)
                
                priority = st.selectbox(
                    "Priority",
                    options=["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(expense_data.get('priority', 'Medium')),
                    help="How essential was this expense?"
                )
                
                tags_default = ", ".join(expense_data.get('tags', [])) if expense_data.get('tags') else ""
                tags = st.text_input(
                    "Tags (comma separated)",
                    value=tags_default,
                    placeholder="restaurant, business, luxury",
                    help="Add tags for better categorization"
                )
            
            notes = st.text_area(
                "Notes",
                value=expense_data.get('notes', ''),
                placeholder="Additional details about this expense...",
                height=100
            )
            
            # CRITICAL FIX: Proper submit button inside form
            submit_text = "💾 Update Expense" if is_edit else "💾 Save Expense"
            submitted = st.form_submit_button(submit_text, use_container_width=True)
            
            # Handle form submission INSIDE the form context
            if submitted:
                if not description or amount <= 0:
                    self.show_toast("❌ Please fill all required fields (*)", "error")
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
                        self.set_loading(True)
                        
                        if is_edit:
                            # Update existing expense
                            response = requests.put(
                                f"{self.backend_url}/expenses/{expense_data['id']}",
                                params={"user_id": st.session_state.user_id},
                                json=expense_payload,
                                timeout=10
                            )
                            success_message = "✅ Expense updated successfully!"
                        else:
                            # Create new expense
                            response = requests.post(
                                f"{self.backend_url}/expenses/",
                                params={"user_id": st.session_state.user_id},
                                json=expense_payload,
                                timeout=10
                            )
                            success_message = "✅ Expense added successfully!"
                        
                        if response.status_code == 200:
                            self.show_toast(success_message, "success")
                            st.balloons()
                            # Clear edit mode
                            st.session_state.edit_expense = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_detail = response.json().get('detail', 'Unknown error')
                            self.show_toast(f"❌ Error: {error_detail}", "error")
                    except Exception as e:
                        self.show_toast(f"🚫 Failed to connect to backend: {e}", "error")
                    finally:
                        self.set_loading(False)
        
        # Add cancel button in edit mode (outside form)
        if is_edit:
            if st.button("❌ Cancel Edit", use_container_width=True):
                st.session_state.edit_expense = None
                self.show_toast("Edit cancelled", "info")
                st.rerun()
    
    def get_expenses(self, start_date=None, end_date=None, category=None, priority=None, search=None):
        """Get expenses with filters"""
        try:
            params = {"user_id": st.session_state.user_id}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if category:
                params['category'] = category
            if priority:
                params['priority'] = priority
            if search:
                params['search'] = search
            
            response = requests.get(f"{self.backend_url}/expenses/", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.show_toast(f"Error fetching expenses: {e}", "error")
        return []
    
    def render_expense_list(self):
        """Render expense list with filters"""
        st.header("📋 Expense List - INR")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            category_filter = st.selectbox("Category", ["All", "Food & Dining", "Transportation", 
                                                        "Entertainment", "Utilities", "Shopping", 
                                                        "Healthcare", "Travel", "Education", "Housing", "Other"])
        with col2:
            priority_filter = st.selectbox("Priority", ["All", "Low", "Medium", "High"])
        with col3:
            search_filter = st.text_input("Search", placeholder="Search description...")
        with col4:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Get expenses
        expenses = self.get_expenses(
            category=category_filter if category_filter != "All" else None,
            priority=priority_filter if priority_filter != "All" else None,
            search=search_filter if search_filter else None
        )
        
        if expenses:
            st.success(f"Found {len(expenses)} expenses")
            
            for expense in expenses:
                with st.expander(f"{expense['date']} - {expense['description']} - {CURRENCY}{expense['amount']:,.2f}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Category:** {expense['category']}")
                        st.write(f"**Priority:** {expense['priority']}")
                    with col2:
                        st.write(f"**Amount:** {CURRENCY}{expense['amount']:,.2f}")
                        st.write(f"**Date:** {expense['date']}")
                    with col3:
                        if expense.get('tags'):
                            st.write(f"**Tags:** {', '.join(expense['tags'])}")
                        if expense.get('notes'):
                            st.write(f"**Notes:** {expense['notes']}")
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_{expense['id']}"):
                            st.session_state.edit_expense = expense
                            st.session_state.page = "Add Expense"
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{expense['id']}"):
                            try:
                                response = requests.delete(
                                    f"{self.backend_url}/expenses/{expense['id']}",
                                    params={"user_id": st.session_state.user_id}
                                )
                                if response.status_code == 200:
                                    self.show_toast("✅ Expense deleted successfully!", "success")
                                    st.rerun()
                                else:
                                    self.show_toast("❌ Failed to delete expense", "error")
                            except Exception as e:
                                self.show_toast(f"❌ Error: {e}", "error")
        else:
            st.info("No expenses found. Add your first expense!")
            if st.button("➕ Add Expense"):
                st.session_state.page = "Add Expense"
                st.rerun()
    
    def render_analytics(self):
        """Render detailed analytics page"""
        st.header("📈 Detailed Analytics - INR")
        
        analytics = self.get_analytics()
        if not analytics:
            st.error("No analytics data available")
            return
        
        # Comprehensive metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Spent", f"{CURRENCY}{analytics.get('total_spent', 0):,.0f}")
        with col2:
            st.metric("Daily Average", f"{CURRENCY}{analytics.get('average_daily', 0):.0f}")
        with col3:
            st.metric("Savings Rate", f"{analytics.get('savings_rate', 0):.1f}%")
        with col4:
            velocity = analytics.get('spending_velocity', {})
            change = velocity.get('change_percentage', 0)
            st.metric("Weekly Change", f"{change:+.1f}%")
        
        st.markdown("---")
        
        # Priority distribution
        st.subheader("Priority Distribution")
        priority_dist = analytics.get('priority_distribution', {})
        if priority_dist:
            fig = px.bar(
                x=list(priority_dist.keys()),
                y=list(priority_dist.values()),
                title="Spending by Priority",
                color=list(priority_dist.keys()),
                color_discrete_map={"High": "red", "Medium": "yellow", "Low": "green"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Category breakdown table
        st.subheader("Category Breakdown")
        category_breakdown = analytics.get('category_breakdown', {})
        if category_breakdown:
            df = pd.DataFrame(list(category_breakdown.items()), columns=['Category', 'Amount'])
            df['Amount'] = df['Amount'].apply(lambda x: f"{CURRENCY}{x:,.2f}")
            df['Percentage'] = (pd.to_numeric(df['Amount'].str.replace(CURRENCY, '').str.replace(',', '')) / 
                               analytics.get('total_spent', 1) * 100).apply(lambda x: f"{x:.1f}%")
            st.dataframe(df, use_container_width=True)
    
    def render_budgets(self):
        """Render budgets page"""
        st.header("💰 Budget Management - INR")
        st.info("Budget features coming soon! Set monthly budgets and track spending.")
    
    def render_export(self):
        """Render export page"""
        st.header("📤 Export Data - INR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Quick Export")
            if st.button("Download All Data", use_container_width=True):
                st.session_state.show_export_modal = True
                st.rerun()
        
        with col2:
            st.subheader("🔄 Initialize Sample Data")
            st.warning("This will add sample expenses for demo purposes")
            if st.button("Load Sample Data", use_container_width=True):
                self.initialize_sample_data()
    
    def run(self):
        """Main application loop"""
        # Render sidebar
        self.render_sidebar()
        
        # Render modals
        self.render_account_modal()
        
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

# Run the application
if __name__ == "__main__":
    tracker = EnhancedExpenseTracker(BACKEND_URL)
    tracker.run()
