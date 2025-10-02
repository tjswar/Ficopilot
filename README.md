# FiCopilot - Public Financial Analysis Tool

An AI-powered financial assistant that enables anyone to upload Excel financial data and ask natural language questions to get instant insights with interactive visualizations.

## Overview

FiCopilot allows users to upload their company's financial data in Excel format and query it using plain English questions. The system analyzes revenue, profitability, expenses, and cash position, providing answers with charts and detailed breakdowns.

## Features

- File Upload**: Upload your own Excel financial data
- Natural Language Queries**: Ask questions in plain English
- 5 Key Financial Metrics**:
  - Revenue vs Budget Analysis with variance
  - Gross Margin calculation and trends
  - Operating Expense breakdown by category
  - EBITDA calculation
  - Cash Runway analysis with burn rate
- **Interactive Charts**: Dynamic Plotly visualizations
- **Data Validation**: Automatic file structure verification
- **Error Handling**: Clear error messages for data issues

## Requirements

- Python 3.8+
- Excel file (.xlsx) with specific structure (see below)

## Installation
```bash
# Clone or download the project
cd FiCopilot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install streamlit pandas openpyxl plotly