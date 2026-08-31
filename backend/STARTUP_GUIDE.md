# Backend Startup & Finance Skills Testing Guide

## Current Status ✅
- **Finance team skills**: Fully integrated (10 skills, 8 knowledge spaces, 6 tools, 3 reasoning strategies)
- **Finance positions**: Complete (accounts_specialist, finance_analyst, budget_analyst)
- **Developer team**: Fixed import paths and empty files
- **Dependencies**: Updated motor/pymongo/pydantic to compatible versions

## Prerequisites

### 1. Install MongoDB (Required for full functionality)
Since MongoDB is not currently installed on your system, you need to install it:

**Option A: Install MongoDB locally**
- Download MongoDB Community Server from https://www.mongodb.com/try/download/community
- Install with default settings
- Start MongoDB service:
  ```powershell
  # Start MongoDB service
  Start-Service MongoDB
  
  # Or run MongoDB directly
  mongod --dbpath "C:\data\db"
  ```

**Option B: Use MongoDB Atlas (Cloud)**
- Create free account at https://www.mongodb.com/cloud/atlas
- Create a free cluster
- Get connection string and update `.env` file

### 2. Install RabbitMQ (Optional for messaging)
```powershell
# Download and install RabbitMQ from https://www.rabbitmq.com/download.html
# Or use Docker: docker run -d -p 5672:5672 rabbitmq
```

## Step-by-Step Startup Guide

### Step 1: Navigate to Backend Directory
```powershell
cd "C:\Users\Piyush Sharma\Documents\mycel_final\backend"
```

### Step 2: Activate Virtual Environment
```powershell
.\venv\Scripts\activate
```

### Step 3: Verify Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment
Create or update `.env` file in the backend directory:
```env
# MongoDB Configuration
mongodb_url=mongodb://localhost:27017/office
mongodb_database=office

# RabbitMQ Configuration
rabbitmq_host=localhost
rabbitmq_port=5672
rabbitmq_user=guest
rabbitmq_password=guest
rabbitmq_vhost=/

# JWT Configuration
jwt_secret_key=your-secret-key-change-in-production
jwt_algorithm=HS256
access_token_expire_minutes=60

# Application Configuration
app_name=Mycel
app_env=development
debug=True
host=0.0.0.0
port=8000
```

### Step 5: Start MongoDB
```powershell
# If using local MongoDB
Start-Service MongoDB

# Verify it's running
mongod --version
```

### Step 6: Seed the Database (Optional - for full functionality)
```powershell
# Seed skills (including finance skills)
python -m workforce.skills.seed

# Seed positions from team definitions
python scripts\seed_positions.py

# Seed knowledge spaces
python scripts\seed_knowledge.py
```

### Step 7: Start the Backend Server
```powershell
python main.py
```

The server will start on `http://127.0.0.1:8000`

## Testing Finance Skills via Swagger Docs

### Access Swagger UI
Open your browser and navigate to:
```
http://127.0.0.1:8000/docs
```

### Test Finance Team Skills

#### 1. List All Skills
- **Endpoint**: `GET /api/v1/skills`
- **Description**: Returns all skills including the new finance skills
- **Expected Result**: Should show 10+ finance skills (accounting, financial_modeling, budgeting, etc.)

#### 2. Filter Skills by Domain
- **Endpoint**: `GET /api/v1/skills?domain=finance`
- **Description**: Returns only finance-related skills
- **Expected Result**: Should show exactly the 10 finance skills we created

#### 3. Get Specific Skill
- **Endpoint**: `GET /api/v1/skills/accounting`
- **Description**: Returns details for the accounting skill
- **Expected Result**: 
  ```json
  {
    "skill_id": "accounting",
    "name": "accounting", 
    "display_name": "Accounting",
    "description": "Ability to maintain financial records...",
    "domain": "finance",
    "category": "technical"
  }
  ```

#### 4. Get Finance Team Skills
- **Endpoint**: `GET /api/v1/teams/finance/skills`
- **Description**: Returns skills assigned to the finance team
- **Expected Result**: Should show the 7 core finance skills

### Test Finance Team Positions

#### 1. List All Positions
- **Endpoint**: `GET /api/v1/positions`
- **Description**: Returns all positions including finance positions
- **Expected Result**: Should show accounts_specialist, finance_analyst, budget_analyst

#### 2. Get Finance Team Positions
- **Endpoint**: `GET /api/v1/teams/finance/positions`
- **Description**: Returns positions specific to the finance team
- **Expected Result**: Should show exactly 3 finance positions

#### 3. Get Specific Position
- **Endpoint**: `GET /api/v1/positions/accounts_specialist`
- **Description**: Returns detailed position requirements
- **Expected Result**: Should show:
  - 6 required skills (accounting, reconciliation, financial_reporting, compliance, data_analysis, cost_analysis)
  - 4 required tools (spreadsheet.processing, financial.calculator, document.generation, database.query)
  - 4 required knowledge spaces (accounting_fundamentals, financial_reporting_standards, regulatory_compliance, audit_procedures)
  - 1 reasoning requirement (financial_validation)

#### 4. Test Other Finance Positions
- **Endpoint**: `GET /api/v1/positions/finance_analyst`
- **Expected Result**: 7 skills, 6 tools, 5 knowledge spaces, financial_analysis_reasoning

- **Endpoint**: `GET /api/v1/positions/budget_analyst`
- **Expected Result**: 7 skills, 5 tools, 4 knowledge spaces, budget_optimization

## Quick Test Without MongoDB

If you want to test the integration without MongoDB:

```powershell
# Run the integration test
python scripts\test_finance_skills.py
```

This will verify:
- All skill definitions are properly structured
- All imports work correctly
- Position requirements are complete
- Capabilities are properly configured

## Troubleshooting

### MongoDB Connection Issues
- **Error**: "MongoDB client is not initialized"
- **Solution**: Ensure MongoDB is running and accessible at the configured URL

### Import Errors
- **Error**: "ModuleNotFoundError: No module named 'individual'"
- **Solution**: Fixed by updating import paths to use relative imports (`.individual`)

### Dependency Conflicts
- **Error**: "ImportError: cannot import name '_QUERY_OPTIONS'"
- **Solution**: Updated motor to 3.7.1 and pymongo to 4.17.0

### AccessMode Errors
- **Error**: "AttributeError: type object 'AccessMode' has no attribute 'READ_WRITE'"
- **Solution**: Changed to use `AccessMode.FULL` instead of `AccessMode.READ_WRITE`

## Summary

Your finance team is now **fully integrated and ready to use**:

✅ **10 Finance Skills**: accounting, financial_modeling, budgeting, data_analysis, reconciliation, financial_reporting, forecasting, risk_assessment, compliance, cost_analysis

✅ **8 Knowledge Spaces**: accounting_fundamentals, financial_analysis, budgeting_principles, financial_reporting_standards, regulatory_compliance, financial_markets, cost_management, audit_procedures

✅ **6 Tools**: spreadsheet.processing, financial.calculator, data.analysis, document_generation, database.query, reporting.tools

✅ **3 Reasoning Strategies**: financial_validation, financial_analysis_reasoning, budget_optimization

✅ **3 Complete Positions**: accounts_specialist, finance_analyst, budget_analyst

Once MongoDB is installed and the backend is running, you can test all of this via the Swagger UI at `http://127.0.0.1:8000/docs`.
