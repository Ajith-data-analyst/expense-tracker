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
BACKEND_URL = os.environ.get("BACKEND_URL", "https://expense-tracker-n6e8.onrender.com")
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
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
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
        
        /* Loading spinner */
        .spinner {
            border: 4px solid #f3f3f3;
            border-radius: 50%;
            border-top: 4px solid #3498db;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
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
        
        /* Toast notification */
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px;
            border-radius: 5px;
            color: white;
            z-index: 1000;
            animation: fadeIn 0.5s, fadeOut 0.5s 2.5s;
        }
        
        .toast.success { background-color: #4CAF50; }
        .toast.error { background-color: #f44336; }
        .toast.warning { background-color: #ff9800; }
        .toast.info { background-color: #2196F3; }
        
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
        
        @keyframes fadeOut {
            from {opacity: 1;}
            to {opacity: 0;}
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<h1 class="main-header">💸 Super Expense Tracker Pro - {CURRENCY}</h1>', unsafe_allow_html=True)
    
    def show_toast(self, message, type="info"):
        """Show toast notification"""
        st.markdown(f"""
        <div class="toast {type}">
            {message}
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.1)  # Allow the toast to render
    
    def test_connection(self):
        """Test connection to backend"""
        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
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
        if 'show_forgot_password' not in st.session_state:
            st.session_state.show_forgot_password = False
        if 'show_reset_password' not in st.session_state:
            st.session_state.show_reset_password = False
        if 'reset_phone' not in st.session_state:
            st.session_state.reset_phone = ""
        if 'show_export_modal' not in st.session_state:
            st.session_state.show_export_modal = False
        if 'loading' not in st.session_state:
            st.session_state.loading = False
    
    def set_loading(self, loading=True):
        """Set loading state"""
        st.session_state.loading = loading
        if loading:
            st.rerun()
    
    def render_footer(self):
        """Render footer with tech stack and copyright"""
        st.markdown("""
        <div class="footer">
            <p><strong>Tech Stack:</strong> FastAPI • Streamlit • Plotly • Pandas</p>
            <p><strong>API:</strong> RESTful JSON API • <strong>Requirements:</strong> Python 3.8+</p>
            <p>© 2024 Expense Tracker Pro. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_loading_spinner(self):
        """Render loading spinner"""
        if st.session_state.loading:
            st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; height: 200px;">
                <div class="spinner"></div>
            </div>
            <p style="text-align: center;">Loading... Please wait</p>
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
                        if (len(reset_code) == 6 and len(new_password) == 6 and 
                            new_password == confirm_password):
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
            response = requests.post(f"{self.backend_url}/sample-data/initialize", params={"user_id": st.session_state.user_id})
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
                
            response = requests.get(f"{self.backend_url}/analytics/overview", params=params, timeout=10)
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
                default_date = (lambda d: datetime.fromisoformat(d) if d else datetime.now())(expense_data.get('date')) if True else datetime.now()
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
    
    def get_expenses(self, **filters):
        """Get expenses from backend with filters"""
        try:
            self.set_loading(True)
            params = {"user_id": st.session_state.user_id, **filters}
            response = requests.get(f"{self.backend_url}/expenses/", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.show_toast(f"Error fetching expenses: {e}", "error")
        finally:
            self.set_loading(False)
        return []
    
    def render_expense_list(self):
        """Render enhanced expense list with advanced filtering"""
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
        with col2:
            if st.button("Clear Search", use_container_width=True):
                st.session_state.search_query = ""
                self.show_toast("Search cleared", "info")
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
                    # Store filters in session state
                    st.session_state.filters = {
                        'category': category_filter if category_filter != "All" else None,
                        'priority': priority_filter if priority_filter != "All" else None,
                        'min_amount': min_amount if min_amount > 0 else None,
                        'max_amount': max_amount if max_amount < 10000 else None,
                        'tags': tags_filter if tags_filter else None,
                        'search': search_query if search_query else None,
                        'date_range': date_range
                    }
                    self.show_toast("✅ Filters applied", "success")
                    st.rerun()
            with col_clear:
                if st.button("Clear All Filters", use_container_width=True):
                    st.session_state.filters = {}
                    st.session_state.search_query = ""
                    self.show_toast("🧹 All filters cleared", "info")
                    st.rerun()
        
        # Build filter parameters
        filters = {}
        if st.session_state.get('filters', {}).get('category'):
            filters['category'] = st.session_state.filters['category']
        if st.session_state.get('filters', {}).get('priority'):
            filters['priority'] = st.session_state.filters['priority']
        if st.session_state.get('filters', {}).get('min_amount'):
            filters['min_amount'] = st.session_state.filters['min_amount']
        if st.session_state.get('filters', {}).get('max_amount'):
            filters['max_amount'] = st.session_state.filters['max_amount']
        if st.session_state.get('filters', {}).get('tags'):
            filters['tags'] = st.session_state.filters['tags']
        if search_query:
            filters['search'] = search_query
        
        # Date range filter
        date_range = st.session_state.get('filters', {}).get('date_range', 'All Time')
        if date_range == "Last 7 Days":
            filters['start_date'] = (datetime.now() - timedelta(days=7)).isoformat()
        elif date_range == "Last 30 Days":
            filters['start_date'] = (datetime.now() - timedelta(days=30)).isoformat()
        elif date_range == "Last 90 Days":
            filters['start_date'] = (datetime.now() - timedelta(days=90)).isoformat()
        
        expenses = self.get_expenses(**filters)
        
        if not expenses:
            st.info("No expenses found matching your filters.")
            return
        
        # Display expenses in an interactive table
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
        
        # Enhanced expense display - Fixed to show newest first
        st.subheader("💳 Expense Details (Newest First)")
        
        for expense in expenses:  # Already sorted by date descending from backend
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
                    # Color code by priority
                    priority_color = {
                        "High": "red", 
                        "Medium": "orange", 
                        "Low": "green"
                    }
                    priority = expense.get('priority', 'Medium')
                    st.write(f":{priority_color.get(priority, 'orange')}[**{priority}**]")
                with col5:
                    st.write(f"**{CURRENCY}{float(expense['amount']):.0f}**")
                    
                    # Action buttons
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{expense['id']}"):
                            st.session_state.edit_expense = expense
                            st.session_state.page = "Add Expense"
                            self.show_toast("Editing expense...", "info")
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{expense['id']}"):
                            self.delete_expense(expense['id'])
                
                st.markdown("---")
    
    def delete_expense(self, expense_id):
        """Delete an expense with confirmation"""
        # Create confirmation dialog
        confirm_key = f"confirm_delete_{expense_id}"
        
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False
        
        if not st.session_state[confirm_key]:
            st.warning(f"⚠️ Are you sure you want to delete this expense?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", key=f"yes_{expense_id}"):
                    st.session_state[confirm_key] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key=f"no_{expense_id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            try:
                self.set_loading(True)
                response = requests.delete(
                    f"{self.backend_url}/expenses/{expense_id}", 
                    params={"user_id": st.session_state.user_id},
                    timeout=10
                )
                if response.status_code == 200:
                    self.show_toast("✅ Expense deleted successfully!", "success")
                    # Clear the confirmation state
                    st.session_state[confirm_key] = False
                    time.sleep(1)
                    st.rerun()
                else:
                    self.show_toast("❌ Failed to delete expense", "error")
                    st.session_state[confirm_key] = False
            except Exception as e:
                self.show_toast(f"❌ Error deleting expense: {e}", "error")
                st.session_state[confirm_key] = False
            finally:
                self.set_loading(False)
    
    def render_analytics(self):
        """Render comprehensive analytics page"""
        st.header("📈 Advanced Analytics - INR")
        
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox(
                "Analysis Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time"]
            )
        
        # Convert period to dates
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
            start_date = datetime(2020, 1, 1)  # Arbitrary early date
        
        analytics = self.get_analytics(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        if not analytics:
            st.info("No data available for analytics")
            return
        
        # Enhanced Analytics Dashboard
        st.subheader("📊 Comprehensive Financial Analysis")
        
        # Row 1: Key Metrics
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
        
        # Row 2: Comparative analysis
        st.subheader("📈 Comparative Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Spending by day of week
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
            # Category distribution
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
        
        # Row 3: Advanced analytics
        st.subheader("🔍 Deep Dive Analytics")
        col1, col2 = st.columns(2)
        
        with col1:
            # Spending velocity
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
            # Priority analysis
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
        
        # Financial Health Score
        st.subheader("🏥 Financial Health Score")
        
        savings_rate = analytics.get('savings_rate', 0)
        health_score = min(100, max(0, savings_rate + 50))  # Simple scoring
        
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
            self.set_loading(True)
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
        
        except Exception as e:
            self.show_toast(f"Error loading budget alerts: {e}", "error")
        finally:
            self.set_loading(False)
        
        # Budget setup interface - NOW WORKING WITH BACKEND
        st.subheader("🎯 Set Custom Budgets")
        
        st.info("Configure your monthly budget limits for each category:")
        
        categories = [
            "Food & Dining", "Transportation", "Entertainment", 
            "Utilities", "Shopping", "Healthcare", 
            "Travel", "Education", "Housing", "Other"
        ]
        
        # Load current budgets from backend
        try:
            self.set_loading(True)
            response = requests.get(f"{self.backend_url}/budgets/{st.session_state.user_id}")
            if response.status_code == 200:
                user_budgets = response.json()
            else:
                user_budgets = {}
        except Exception as e:
            self.show_toast(f"Error loading budgets: {e}", "error")
            user_budgets = {}
        finally:
            self.set_loading(False)
        
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
                # Use user_budgets if available, else default_budgets
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
                self.set_loading(True)
                response = requests.post(
                    f"{self.backend_url}/budgets/{st.session_state.user_id}",
                    json=budget_values
                )
                if response.status_code == 200:
                    self.show_toast("✅ Budget limits saved successfully!", "success")
                    st.rerun()
                else:
                    self.show_toast("❌ Failed to save budgets", "error")
            except Exception as e:
                self.show_toast(f"❌ Error saving budgets: {e}", "error")
            finally:
                self.set_loading(False)
    
    def render_export(self):
        """Render data export page with working functionality"""
        st.header("📤 Data Export & Reports - INR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export Options")
            export_format = st.selectbox("Format", ["JSON", "CSV"])
            
            # Date range for export
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="export_start")
            end_date = st.date_input("End Date", datetime.now(), key="export_end")
            
            if st.button("📥 Generate Export", use_container_width=True):
                try:
                    self.set_loading(True)
                    response = requests.get(
                        f"{self.backend_url}/reports/export",
                        params={
                            "user_id": st.session_state.user_id,
                            "format": export_format.lower(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat()
                        },
                        timeout=10
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
                        
                        self.show_toast("✅ Export generated successfully!", "success")
                    else:
                        self.show_toast(f"❌ Failed to generate export: {response.status_code}", "error")
                    
                except Exception as e:
                    self.show_toast(f"❌ Error generating export: {e}", "error")
                finally:
                    self.set_loading(False)
        
        with col2:
            st.subheader("Quick Reports")
            
            report_type = st.selectbox(
                "Report Type",
                ["Spending Summary", "Category Analysis", "Monthly Report", "Budget vs Actual"]
            )
            
            if st.button("📊 Generate Report", use_container_width=True):
                try:
                    self.set_loading(True)
                    # Generate actual report data
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
                            # Convert amount to float for calculations
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
                            # Get budget alerts for actual comparison
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
                    self.show_toast(f"❌ Error generating report: {e}", "error")
                finally:
                    self.set_loading(False)
    
    def run(self):
        """Main method to run the enhanced application"""
        # Check backend connection
        if not self.test_connection():
            st.error("🚫 Cannot connect to backend server. Please make sure the FastAPI server is running")
            st.info("💡 Backend URL: " + self.backend_url)
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
        
        # Render footer
        self.render_footer()

# Run the application
if __name__ == "__main__":
    app = EnhancedExpenseTracker(BACKEND_URL)
    app.run()
