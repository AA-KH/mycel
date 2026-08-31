# Legal Team Setup Guide

## ✅ Legal Team Created Successfully

The legal team has been fully configured with all necessary components for Indian legal jurisdiction.

## 📊 Current Status

### Structure Validation: ✅ PASSED
- 46 files created and validated
- All required fields present
- Directory structure complete
- Configuration files in place

### Team Components
- **6 Positions**: Senior Lawyer, Legal Analyst, Contract Specialist, Compliance Analyst, Legal Researcher, Legal Reviewer
- **6 Core Skills**: Legal Research, Document Analysis, Contract Analysis, Compliance Analysis, Legal Writing, Citation Validation
- **5 Knowledge Spaces**: Indian Legal System, Indian Statutes, Indian Regulations, Indian Case Law, Legal Terminology
- **5 Legal Tools**: Legal Document Parser, RAG Retrieval, Document Search, Citation Tools, Document Generation
- **2 Reasoning Strategies**: Legal Authority Verification, Compliance Risk Assessment
- **4 Pipelines**: Main Legal Pipeline, Legal Research Pipeline, Contract Review Pipeline, Compliance Pipeline
- **6 Team Members**: Vikram Singh, Raghav Mehta, Isha Verma, Priya Nair, Aditi Sharma, Armaan Kapoor

## 🚀 To Enable Full LLM Functionality with Groq API

### Step 1: Install Groq Package
```bash
pip install groq
```

### Step 2: Configure Environment Variables
Add to your `.env` file:
```env
GROQ_API_KEY_1=your_groq_api_key_here
GROQ_API_KEY_2=your_backup_groq_api_key_here
```

Get your API keys from: https://console.groq.com/

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Tests

#### Structure Test (No API Key Required)
```bash
python scripts/test_legal_structure.py
```

#### Demo (No API Key Required)
```bash
python scripts/legal_team_demo.py
```

#### Full Integration Test (Requires API Key)
```bash
python scripts/test_legal_with_groq.py
```

## 📁 File Structure

```
backend/teams/legal/
├── __init__.py
├── team.py
├── LEGAL_TEAM_CONFIG.md
├── common/
│   ├── __init__.py
│   ├── capabilities.py
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── skills.py
│   │   └── individual/
│   │       ├── legal_research.py
│   │       ├── document_analysis.py
│   │       ├── contract_analysis.py
│   │       ├── compliance_analysis.py
│   │       ├── legal_writing.py
│   │       └── citation_validation.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   └── individual/
│   │       ├── legal_document_parser.py
│   │       ├── rag_retrieval.py
│   │       ├── document_search.py
│   │       ├── citation_tools.py
│   │       └── document_generation.py
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── knowledge.py
│   │   └── individual/
│   │       ├── indian_legal_system.py
│   │       ├── indian_statutes.py
│   │       ├── indian_regulations.py
│   │       ├── indian_case_law.py
│   │       └── legal_terminology.py
│   └── reasoning/
│       ├── __init__.py
│       ├── reasoning.py
│       └── individual/
│           ├── legal_authority_verification.py
│           └── compliance_risk_assessment.py
├── positions/
│   ├── __init__.py
│   ├── legal_analyst.py
│   ├── contract_specialist.py
│   ├── compliance_analyst.py
│   ├── legal_researcher.py
│   ├── legal_reviewer.py
│   └── senior_lawyer.py
├── team_members/
│   ├── __init__.py
│   ├── emp_leg_analyst_001.py
│   ├── emp_leg_contract_001.py
│   ├── emp_leg_researcher_001.py
│   ├── emp_leg_reviewer_001.py
│   ├── emp_leg_senior_001.py
│   ├── emp_leg_compliance_001.py
│   └── baseline/
│       ├── __init__.py
│       ├── legal_analyst.py
│       ├── contract_specialist.py
│       ├── compliance_analyst.py
│       ├── legal_researcher.py
│       ├── legal_reviewer.py
│       └── senior_lawyer.py
└── pipelines/
    ├── __init__.py
    ├── legal_pipeline.py
    ├── legal_research.py
    ├── contract_review_pipeline.py
    └── compliance_pipeline.py
```

## 🔧 Configuration Details

### Team Configuration
- **Team ID**: legal
- **Name**: Legal Team
- **Description**: Legal research, document analysis and jurisdiction-aware legal drafting
- **Company**: mycel_global
- **Jurisdiction**: Indian Legal System

### Position Examples

#### Senior Lawyer
- **Headcount**: 1-3 (recommended: 1)
- **Seniority**: Senior
- **Criticality**: High
- **Skills**: All 6 core skills at 80-90% proficiency
- **Role**: Legal strategy and advisory

#### Legal Analyst
- **Headcount**: 1-10 (recommended: 3)
- **Seniority**: Mid
- **Criticality**: High
- **Skills**: Legal research, document analysis, contract analysis
- **Role**: Document analysis and legal insights

## 🎯 Next Steps

1. **Set up Groq API key** in `.env` file
2. **Test the integration** with `python scripts/test_legal_with_groq.py`
3. **Configure MongoDB** connection for data persistence
4. **Start the backend server** to use the legal team through API endpoints
5. **Refer to LEGAL_TEAM_CONFIG.md** for detailed configuration

## 📖 Documentation

Full configuration details are available in:
- `teams/legal/LEGAL_TEAM_CONFIG.md` - Complete team configuration
- `scripts/legal_team_demo.py` - Interactive demonstration
- `scripts/test_legal_structure.py` - Structure validation

## ✨ Features

The legal team is configured to handle:
- **Legal Research**: Case law, statutes, and precedent research
- **Contract Analysis**: Contract drafting and review
- **Compliance Analysis**: Regulatory compliance assessment
- **Document Analysis**: Complex legal document analysis
- **Legal Writing**: Drafting legally binding texts
- **Citation Validation**: Ensuring proper legal citation formats

All operations are designed to work with Groq API for fast LLM inference and are specifically optimized for Indian legal jurisdiction.