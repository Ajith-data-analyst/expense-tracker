import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from datetime import datetime, timedelta
import json
import io

# Configuration
BACKEND_URL = "http://localhost:8000"

class EnhancedExpenseTracker:
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.setup_page()
        
    def setup_page(self):
        """Configure Streamlit page settings with enhanced styling"""
        st.set_page_config(
            page_title="💰 Super Expense Tracker Pro",
            page_icon="💸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for enhanced styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
        }
        .alert-critical { background-color: #ff4b4b; padding: 10px; border-radius: 5px; color: white; }
        .alert-warning { background-color: #ffa500; padding: 10px; border-radius: 5px; color: white; }
        .alert-info { background-color: #4b8aff; padding: 10px; border-radius: 5px; color: white; }
        .expense-card { 
            background-color: #f0f2f6; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 10px 0;
            border-left: 5px solid #1f77b4;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-header">💸 Super Expense Tracker Pro</h1>', unsafe_allow_html=True)
    
    def test_connection(self):
        """Test connection to backend"""
        try:
            response = requests.get(f"{self.backend_url}/")
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
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Spent", f"${analytics['total_spent']:,.2f}")
                    with col2:
                        st.metric("Daily Avg", f"${analytics['average_daily']:.2f}")
            except:
                st.info("Connect to backend to see stats")
    
    def get_analytics(self, start_date=None, end_date=None):
        """Get analytics from backend"""
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            response = requests.get(f"{self.backend_url}/analytics/overview", params=params)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def render_dashboard(self):
        """Render comprehensive dashboard"""
        st.header("📊 Financial Dashboard")
        
        # Date range filter
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        with col3:
            st.write("")  # Spacer
            if st.button("Apply Filter"):
                st.session_state.filters = {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()}
        
        analytics = self.get_analytics(
            start_date=start_date.isoformat(), 
            end_date=end_date.isoformat()
        )
        
        if not analytics:
            st.error("No data available for the selected period")
            return
        
        # Key Metrics
        st.subheader("📈 Key Financial Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Spent", f"${analytics['total_spent']:,.2f}")
        with col2:
            st.metric("Daily Average", f"${analytics['average_daily']:.2f}")
        with col3:
            st.metric("Expense Count", len(self.get_expenses()))
        with col4:
            categories = len(analytics['category_breakdown'])
            st.metric("Categories Used", categories)
        
        # Top row charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Category breakdown pie chart
            if analytics['category_breakdown']:
                fig = px.pie(
                    values=list(analytics['category_breakdown'].values()),
                    names=list(analytics['category_breakdown'].keys()),
                    title="Spending by Category",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Monthly trend
            if analytics['monthly_trend']:
                df_trend = pd.DataFrame(analytics['monthly_trend'])
                fig = px.line(
                    df_trend, 
                    x='month', 
                    y='amount',
                    title="Monthly Spending Trend",
                    markers=True
                )
                fig.update_traces(line=dict(color='#1f77b4', width=3))
                st.plotly_chart(fig, use_container_width=True)
        
        # Second row charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Weekly spending
            if analytics['weekly_spending']:
                df_weekly = pd.DataFrame(analytics['weekly_spending'])
                fig = px.bar(
                    df_weekly,
                    x='week',
                    y='amount',
                    title="Weekly Spending (Last 8 Weeks)",
                    color='amount',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Priority distribution
            if analytics['priority_distribution']:
                fig = px.bar(
                    x=list(analytics['priority_distribution'].keys()),
                    y=list(analytics['priority_distribution'].values()),
                    title="Spending by Priority Level",
                    color=list(analytics['priority_distribution'].keys()),
                    color_discrete_map={
                        'High': '#ff4b4b',
                        'Medium': '#ffa500', 
                        'Low': '#4b8aff'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top expenses table
        st.subheader("🏆 Top 10 Largest Expenses")
        if analytics['top_expenses']:
            top_df = pd.DataFrame(analytics['top_expenses'])
            top_df = top_df[['date', 'description', 'category', 'amount', 'priority']]
            top_df['amount'] = top_df['amount'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(top_df, use_container_width=True)
    
    def render_add_expense(self):
        """Render enhanced expense addition form"""
        st.header("➕ Add New Expense")
        
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                description = st.text_input(
                    "Description *", 
                    placeholder="e.g., Dinner at Italian Restaurant",
                    help="Enter a clear description of the expense"
                )
                amount = st.number_input(
                    "Amount *", 
                    min_value=0.01, 
                    step=0.01, 
                    format="%.2f",
                    help="Enter the expense amount"
                )
                category = st.selectbox(
                    "Category *",
                    options=[
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", 
                        "Travel", "Education", "Housing", "Other"
                    ]
                )
            
            with col2:
                date = st.date_input("Date *", datetime.now())
                priority = st.selectbox(
                    "Priority",
                    options=["Low", "Medium", "High"],
                    help="How essential was this expense?"
                )
                tags = st.text_input(
                    "Tags (comma separated)",
                    placeholder="restaurant, business, luxury",
                    help="Add tags for better categorization"
                )
                notes = st.text_area(
                    "Notes", 
                    placeholder="Additional details about this expense...",
                    height=100
                )
            
            submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
            
            if submitted:
                if not description or amount <= 0:
                    st.error("Please fill all required fields (*)")
                else:
                    expense_data = {
                        "description": description,
                        "amount": float(amount),
                        "category": category,
                        "date": date.isoformat(),
                        "priority": priority,
                        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                        "notes": notes if notes else None
                    }
                    
                    try:
                        response = requests.post(f"{self.backend_url}/expenses/", json=expense_data)
                        if response.status_code == 200:
                            st.success("✅ Expense added successfully!")
                            st.balloons()
                        else:
                            st.error(f"Error adding expense: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"🚫 Failed to connect to backend: {e}")
    
    def get_expenses(self, **filters):
        """Get expenses from backend with filters"""
        try:
            response = requests.get(f"{self.backend_url}/expenses/", params=filters)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def render_expense_list(self):
        """Render enhanced expense list with advanced filtering"""
        st.header("📋 Expense Management")
        
        # Advanced filters
        with st.expander("🔍 Advanced Filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.selectbox(
                    "Category Filter",
                    ["All"] + [
                        "Food & Dining", "Transportation", "Entertainment", 
                        "Utilities", "Shopping", "Healthcare", 
                        "Travel", "Education", "Housing", "Other"
                    ]
                )
                priority_filter = st.selectbox(
                    "Priority Filter", 
                    ["All", "Low", "Medium", "High"]
                )
            
            with col2:
                min_amount = st.number_input("Min Amount", min_value=0.0, value=0.0, step=10.0)
                max_amount = st.number_input("Max Amount", min_value=0.0, value=1000.0, step=10.0)
            
            with col3:
                tags_filter = st.text_input("Tags Filter", placeholder="restaurant, business")
                date_range = st.selectbox(
                    "Date Range",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"]
                )
        
        # Build filter parameters
        filters = {}
        if category_filter != "All":
            filters['category'] = category_filter
        if priority_filter != "All":
            filters['priority'] = priority_filter
        if min_amount > 0:
            filters['min_amount'] = min_amount
        if max_amount > 0:
            filters['max_amount'] = max_amount
        if tags_filter:
            filters['tags'] = tags_filter
        
        # Date range filter
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
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['amount'] = df['amount'].round(2)
        
        # Summary
        st.subheader(f"📊 Summary ({len(expenses)} expenses)")
        total_amount = df['amount'].sum()
        avg_amount = df['amount'].mean()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", f"${total_amount:,.2f}")
        col2.metric("Average", f"${avg_amount:.2f}")
        col3.metric("Largest", f"${df['amount'].max():.2f}")
        
        # Enhanced expense display
        st.subheader("💳 Expense Details")
        
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
                        tags_str = " ".join([f"🏷️{tag}" for tag in expense['tags']])
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
                    st.write(f":{priority_color[expense['priority']]}[**{expense['priority']}**]")
                with col5:
                    st.write(f"**${expense['amount']:.2f}**")
                    
                    # Action buttons
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{expense['id']}"):
                            st.session_state.edit_expense = expense
                            st.session_state.page = "Add Expense"
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{expense['id']}"):
                            self.delete_expense(expense['id'])
                
                st.markdown("---")
    
    def delete_expense(self, expense_id):
        """Delete an expense"""
        try:
            response = requests.delete(f"{self.backend_url}/expenses/{expense_id}")
            if response.status_code == 200:
                st.success("Expense deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete expense")
        except Exception as e:
            st.error(f"Error deleting expense: {e}")
    
    def render_analytics(self):
        """Render comprehensive analytics page"""
        st.header("📈 Advanced Analytics")
        
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox(
                "Analysis Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "All Time"]
            )
        with col2:
            chart_type = st.selectbox(
                "Chart Type",
                ["Bar", "Line", "Area", "Scatter"]
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
        
        # Comparative analysis
        st.subheader("📊 Comparative Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Spending by day of week
            expenses = self.get_expenses(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            if expenses:
                df = pd.DataFrame(expenses)
                df['date'] = pd.to_datetime(df['date'])
                df['day_of_week'] = df['date'].dt.day_name()
                
                daily_avg = df.groupby('day_of_week')['amount'].mean().reindex([
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
                ])
                
                fig = px.bar(
                    x=daily_avg.index,
                    y=daily_avg.values,
                    title="Average Spending by Day of Week",
                    color=daily_avg.values,
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Category comparison over time
            if analytics['monthly_trend'] and analytics['category_breakdown']:
                # This would require more detailed data from the backend
                st.info("Category trend analysis would show here with enhanced backend")
        
        # Predictive analytics placeholder
        st.subheader("🔮 Spending Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Projected Monthly", 
                f"${analytics['average_daily'] * 30:.2f}",
                delta=f"${analytics['average_daily'] * 30 - analytics['total_spent']:.2f}"
            )
        with col2:
            # Simple trend analysis
            if len(analytics['monthly_trend']) > 1:
                recent = analytics['monthly_trend'][-1]['amount']
                previous = analytics['monthly_trend'][-2]['amount'] if len(analytics['monthly_trend']) > 1 else recent
                trend = ((recent - previous) / previous) * 100 if previous > 0 else 0
                st.metric("Monthly Trend", f"{tred:+.1f}%")
        with col3:
            st.metric("Savings Potential", f"${analytics['total_spent'] * 0.1:.2f}")
    
    def render_budgets(self):
        """Render budget management page"""
        st.header("💰 Budget Management & Alerts")
        
        try:
            response = requests.get(f"{self.backend_url}/budgets/alerts")
            if response.status_code == 200:
                alerts = response.json()
                
                if not alerts:
                    st.success("🎉 All budgets are within limits!")
                    return
                
                st.subheader("⚠️ Budget Alerts")
                
                for alert in alerts:
                    if alert['alert_level'] == "Critical":
                        st.markdown(f'<div class="alert-critical">🚨 CRITICAL: {alert["category"]} - ${alert["spent"]:.2f} / ${alert["budget"]:.2f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
                    elif alert['alert_level'] == "Warning":
                        st.markdown(f'<div class="alert-warning">⚠️ WARNING: {alert["category"]} - ${alert["spent"]:.2f} / ${alert["budget"]:.2f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="alert-info">ℹ️ INFO: {alert["category"]} - ${alert["spent"]:.2f} / ${alert["budget"]:.2f} ({alert["percentage"]:.1f}%)</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error loading budget alerts: {e}")
        
        # Budget setup interface
        st.subheader("🎯 Set Custom Budgets")
        
        st.info("Configure your monthly budget limits for each category:")
        
        categories = [
            "Food & Dining", "Transportation", "Entertainment", 
            "Utilities", "Shopping", "Healthcare", 
            "Travel", "Education", "Housing", "Other"
        ]
        
        cols = st.columns(2)
        for i, category in enumerate(categories):
            with cols[i % 2]:
                st.number_input(
                    f"{category} Budget",
                    min_value=0.0,
                    value=500.0,
                    step=50.0,
                    key=f"budget_{category}"
                )
        
        if st.button("💾 Save Budgets", use_container_width=True):
            st.success("Budget limits saved! (Note: This is a demo - implement persistence as needed)")
    
    def render_export(self):
        """Render data export page"""
        st.header("📤 Data Export & Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export Options")
            export_format = st.selectbox("Format", ["JSON", "CSV"])
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            end_date = st.date_input("End Date", datetime.now())
            
            if st.button("📥 Generate Export", use_container_width=True):
                try:
                    response = requests.get(
                        f"{self.backend_url}/reports/export",
                        params={
                            "format": export_format.lower(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat()
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if export_format == "CSV":
                            csv_data = data['csv']
                            st.download_button(
                                label="📋 Download CSV",
                                data=csv_data,
                                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            json_str = json.dumps(data, indent=2)
                            st.download_button(
                                label="📄 Download JSON",
                                data=json_str,
                                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json"
                            )
                        
                        st.success("Export generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating export: {e}")
        
        with col2:
            st.subheader("Quick Reports")
            
            report_type = st.selectbox(
                "Report Type",
                ["Spending Summary", "Category Analysis", "Monthly Report"]
            )
            
            if st.button("📊 Generate Report", use_container_width=True):
                st.info(f"Generating {report_type}... (This would create a detailed PDF report in a real application)")
                
                # Placeholder for report generation
                expenses = self.get_expenses()
                if expenses:
                    df = pd.DataFrame(expenses)
                    st.dataframe(df.describe(), use_container_width=True)
    
    def run(self):
        """Main method to run the enhanced application"""
        # Check backend connection
        if not self.test_connection():
            st.error("🚫 Cannot connect to backend server. Please make sure the FastAPI server is running on localhost:8000")
            st.info("💡 To start the backend server, run: `python backend.py`")
            return
        
        # Initialize session state
        self.initialize_session_state()
        
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

# Run the application
if __name__ == "__main__":
    app = EnhancedExpenseTracker(BACKEND_URL)
    app.run()