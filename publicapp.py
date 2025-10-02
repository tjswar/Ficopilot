import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px
import re

# Session state to store uploaded file
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

st.title("💼 FICOPILOT ")
st.write("Upload your financial data and ask questions!")

# File upload section
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel file (.xlsx)", 
    type=['xlsx'],
    help="File must contain 4 sheets: actuals, budget, cash, fx"
)

if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file
    
    # Validate file structure
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        required_sheets = ['actuals', 'budget', 'cash', 'fx']
        missing_sheets = [s for s in required_sheets if s not in excel_file.sheet_names]
        
        if missing_sheets:
            st.sidebar.error(f"❌ Missing sheets: {', '.join(missing_sheets)}")
            st.sidebar.warning("Please check the file format requirements below!")
        else:
            st.sidebar.success("✅ File uploaded successfully!")
            
            # Show file info
            actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
            date_range = f"{actuals['month'].min()} to {actuals['month'].max()}"
            st.sidebar.info(f"📅 Data range: {date_range}")
            st.sidebar.info(f"📊 Total records: {len(actuals)}")
            
    except Exception as e:
        st.sidebar.error(f"❌ Error reading file: {str(e)}")
        st.sidebar.warning("Please check the file format requirements below!")

# Helper functions
def extract_month_from_question(question):
    month_map = {
        'january': '01', 'february': '02', 'march': '03',
        'april': '04', 'may': '05', 'june': '06',
        'july': '07', 'august': '08', 'september': '09',
        'october': '10', 'november': '11', 'december': '12'
    }
    
    question_lower = question.lower()
    
    pattern1 = r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
    match1 = re.search(pattern1, question_lower)
    if match1:
        month_name = match1.group(1)
        year = match1.group(2)
        month_num = month_map[month_name]
        return f"{year}-{month_num}"
    
    pattern2 = r'(\d{4})-(\d{2})'
    match2 = re.search(pattern2, question)
    if match2:
        return match2.group(0)
    
    return None

def get_revenue_vs_budget(uploaded_file, month):
    actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
    budget = pd.read_excel(uploaded_file, sheet_name='budget')
    
    month_data = actuals[actuals['month'] == month]
    revenue_data = month_data[month_data['account_category'] == 'Revenue']
    actual_revenue = revenue_data['amount'].sum()
   
    budget_month_data = budget[budget['month'] == month]
    budget_revenue_data = budget_month_data[budget_month_data['account_category'] == 'Revenue']
    budget_revenue = budget_revenue_data['amount'].sum()
   
    variance = actual_revenue - budget_revenue
    variance_pct = (variance / budget_revenue * 100) if budget_revenue != 0 else 0.0
    
    fig = go.Figure(data=[
        go.Bar(name='Actual', x=['Revenue'], y=[actual_revenue], marker_color='#2E86AB'),
        go.Bar(name='Budget', x=['Revenue'], y=[budget_revenue], marker_color='#A23B72')
    ])
    fig.update_layout(title=f'Revenue vs Budget - {month}', barmode='group', yaxis_title='Amount ($)', height=400)
    
    text = f"""Revenue vs Budget for {month}:
    Actual: ${actual_revenue:,.0f}
    Budget: ${budget_revenue:,.0f}
    Variance: ${variance:,.0f} ({variance_pct:.1f}%)"""
    
    return {"text": text, "chart": fig}

def get_gross_margin(uploaded_file, month):
    actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
    month_data = actuals[actuals['month'] == month]
    
    revenue_data = month_data[month_data['account_category'] == 'Revenue']
    total_revenue = revenue_data['amount'].sum()
   
    cogs_data = month_data[month_data['account_category'] == 'COGS']
    total_cogs = cogs_data['amount'].sum()
   
    gross_margin = total_revenue - total_cogs
    gross_margin_pct = (gross_margin / total_revenue * 100) if total_revenue != 0 else 0.0
    
    fig = go.Figure(data=[
        go.Bar(name='Revenue', x=[''], y=[total_revenue], marker_color='#06A77D'),
        go.Bar(name='COGS', x=[''], y=[total_cogs], marker_color='#D4636D'),
        go.Bar(name='Gross Profit', x=[''], y=[gross_margin], marker_color='#F18F01')
    ])
    fig.update_layout(title=f'Gross Margin - {month}', yaxis_title='Amount ($)', height=400)
    
    text = f"""Gross Margin for {month}:
    Total Revenue: ${total_revenue:,.0f}
    Total COGS: ${total_cogs:,.0f}
    Gross Margin: ${gross_margin:,.0f} ({gross_margin_pct:.1f}%)"""
    
    return {"text": text, "chart": fig}

def get_opex_breakdown(uploaded_file, month):
    actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
    month_data = actuals[actuals['month'] == month]
    
    opex_data = month_data[month_data['account_category'].str.startswith('Opex:')]
    total_opex = opex_data['amount'].sum()
    
    if total_opex == 0:
        return {"text": f"No Opex data available for {month}.", "chart": None}
    
    breakdown = opex_data.groupby('account_category')['amount'].sum().reset_index()
    breakdown = breakdown.sort_values(by='amount', ascending=False)
    breakdown['pct'] = (breakdown['amount'] / total_opex) * 100
    
    fig = px.pie(breakdown, values='amount', names='account_category', 
                 title=f'Opex Breakdown - {month}', hole=0.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    breakdown_lines = [f"  - {row['account_category']}: ${row['amount']:,.0f} ({row['pct']:.1f}%)" 
                       for _, row in breakdown.iterrows()]
    text = f"""Opex Breakdown for {month} (Total: ${total_opex:,.0f}):
{chr(10).join(breakdown_lines)}"""
    
    return {"text": text, "chart": fig}

def get_ebitda(uploaded_file, month):
    actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
    month_data = actuals[actuals['month'] == month]
    
    revenue = month_data[month_data['account_category'] == 'Revenue']['amount'].sum()
    cogs = month_data[month_data['account_category'] == 'COGS']['amount'].sum()
    opex = month_data[month_data['account_category'].str.startswith('Opex:')]['amount'].sum()
    ebitda = revenue - cogs - opex
    
    text = f"""EBITDA for {month}:
    Revenue: ${revenue:,.0f}
    COGS: ${cogs:,.0f}
    Opex: ${opex:,.0f}
    EBITDA: ${ebitda:,.0f}"""
    
    return {"text": text, "chart": None}

def get_cash_runway(uploaded_file, month):
    cash_sheet = pd.read_excel(uploaded_file, sheet_name='cash')
    actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
    
    current_cash_row = cash_sheet[cash_sheet['month'] == month]
    if current_cash_row.empty:
        return {"text": "No cash data available for this month.", "chart": None}
    current_cash = current_cash_row['cash_usd'].values[0]
    
    month_dt = pd.to_datetime(month)
    last_3_months = [
        (month_dt - pd.DateOffset(months=2)).strftime('%Y-%m'),
        (month_dt - pd.DateOffset(months=1)).strftime('%Y-%m'),
        month
    ]
    
    burns = []
    for m in last_3_months:
        m_data = actuals[actuals['month'] == m]
        revenue = m_data[m_data['account_category'] == 'Revenue']['amount'].sum()
        cogs = m_data[m_data['account_category'] == 'COGS']['amount'].sum()
        opex = m_data[m_data['account_category'].str.startswith('Opex:')]['amount'].sum()
        burns.append(-(revenue - cogs - opex))
    
    avg_burn = sum(burns) / len(burns)
    
    cash_trend = cash_sheet.sort_values('month')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cash_trend['month'], y=cash_trend['cash_usd'], 
                             mode='lines+markers', name='Cash', line=dict(color='#06A77D', width=3)))
    fig.update_layout(title='Cash Position Over Time', xaxis_title='Month', yaxis_title='Cash (USD)', height=400)
    
    if avg_burn <= 0:
        text = f"Company is profitable (no burn). Current Cash: ${current_cash:,.0f}"
    else:
        runway = current_cash / avg_burn
        text = f"""Cash Runway for {month}:
Current Cash: ${current_cash:,.0f}
Avg Monthly Burn: ${avg_burn:,.0f}
Runway: {runway:.1f} months"""
    
    return {"text": text, "chart": fig}

def answer_question(uploaded_file, question):
    month = extract_month_from_question(question)
    if not month:
        return {"text": "Sorry, I couldn't understand the month.", "chart": None}
    
    q_lower = question.lower()
    
    if 'budget' in q_lower:
        return get_revenue_vs_budget(uploaded_file, month)
    elif 'margin' in q_lower:
        return get_gross_margin(uploaded_file, month)
    elif 'opex' in q_lower:
        return get_opex_breakdown(uploaded_file, month)
    elif 'ebitda' in q_lower:
        return get_ebitda(uploaded_file, month)
    elif 'runway' in q_lower or 'cash' in q_lower:
        return get_cash_runway(uploaded_file, month)
    elif 'revenue' in q_lower:
        actuals = pd.read_excel(uploaded_file, sheet_name='actuals')
        revenue = actuals[(actuals['month'] == month) & 
                         (actuals['account_category'] == 'Revenue')]['amount'].sum()
        return {"text": f"Revenue for {month}: ${revenue:,.0f}", "chart": None}
    else:
        return {"text": "I can answer about: revenue, budget, margin, opex, EBITDA, cash runway", "chart": None}

# Main interface
if st.session_state.uploaded_file is not None:
    question = st.text_input("Your question:", placeholder="What was June 2025 revenue vs budget?")
    
    if st.button("Ask") or question:
        if question:
            with st.spinner("Analyzing..."):
                try:
                    answer = answer_question(st.session_state.uploaded_file, question)
                    st.write(answer["text"])
                    if answer["chart"]:
                        st.plotly_chart(answer["chart"], use_container_width=True)
                except KeyError as e:
                    st.error(f"Column not found: {e}. Please check your file format matches the requirements below.")
                except Exception as e:
                    st.error(f"Error: {str(e)}. Please verify your data format.")
        else:
            st.warning("Please enter a question!")
    
    # Examples
    with st.expander("📖 Example Questions"):
        st.write("- What was revenue in June 2025?")
        st.write("- Show me June 2025 revenue vs budget")
        st.write("- What's the gross margin for 2025-06?")
        st.write("- Break down Opex for June 2025")
        st.write("- What's the cash runway for June 2025?")
else:
    st.info("👆 Please upload an Excel file to get started!")

# Detailed format requirements
with st.expander("📋 REQUIRED FILE FORMAT (Click to expand)"):
    st.markdown("""
     ⚠️ Your Excel file MUST follow this exact structure:
    
    ---
    
    Required: 4 Sheets with exact names (lowercase)
    
     1️⃣ Sheet name: **actuals**
    Monthly actual financial performance
    
    | Column Name | Type | Example | Description |
    |------------|------|---------|-------------|
    | month | date | 2023-01 | YYYY-MM format |
    | entity | text | ParentCo | Company entity |
    | account_category | text | Revenue | Revenue, COGS, or Opex:CategoryName |
    | amount | number | 380000 | Dollar amount |
    | currency | text | USD | Currency code |
    
    Example rows:
                2023-01, ParentCo, Revenue, 380000, USD
                2023-01, ParentCo, COGS, 57000, USD
                2023-01, ParentCo, Opex:Marketing, 76000, USD
                2023-01, ParentCo, Opex:Sales, 45600, USD
                ---
    
     2️⃣ Sheet name: budget
    Same exact structure as actuals (budgeted amounts)
    
    ---
    
     3️⃣ Sheet name: **cash**
    Monthly cash balances
    
    | Column Name | Type | Example | Description |
    |------------|------|---------|-------------|
    | month | date | 2023-01 | YYYY-MM format |
    | entity | text | Consolidated | Company entity |
    | cash_usd | number | 6000000 | Cash in USD |
    
    ---
    
     4️⃣ Sheet name: **fx**
    Foreign exchange rates
    
    | Column Name | Type | Example | Description |
    |------------|------|---------|-------------|
    | month | date | 2023-01 | YYYY-MM format |
    | currency | text | EUR | Currency code |
    | rate_to_usd | number | 1.085 | Rate to USD |
    
    ---
    
     🎯 Critical Rules:
    
    1. Sheet Names: Must be EXACTLY `actuals`, `budget`, `cash`, `fx` (lowercase, no spaces)
    2. Column Names: Must match EXACTLY as shown (case-sensitive)
    3. Month Format: Must be YYYY-MM (e.g., 2023-01, 2025-06)
    4. Operating Expenses: Must start with `Opex:` (e.g., `Opex:Marketing`, `Opex:Sales`, `Opex:R&D`, `Opex:G&A`)
    5. Revenue Category: Must be exactly `Revenue`
    6. COGS Category: Must be exactly `COGS`
    
    ---
    
     💡 Tips:
    - Use the uploaded sample file as a template
    - Check spelling carefully (especially sheet names)
    - Ensure dates are formatted as YYYY-MM
    - All Opex categories must start with "Opex:"
    """)

st.divider()
st.caption("Built with Streamlit • FICOPILOT © 2024")