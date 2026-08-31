# Legal Team Configuration

## Team Overview
- **Team ID**: legal
- **Name**: Legal Team
- **Description**: Legal research, document analysis and jurisdiction-aware legal drafting
- **Company**: mycel_global
- **Status**: Active

## Core Capabilities

### Skills
- legal_research: Researching case law, statutes, and legal precedents
- document_analysis: Analyzing complex legal documents
- contract_analysis: Reviewing and dissecting contract terms
- compliance_analysis: Verifying adherence to regulatory requirements
- legal_writing: Drafting legally binding texts
- citation_validation: Ensuring proper legal citation formats and authority

### Tools
- legal_document_parser: Parsing legal documents
- rag_retrieval: Retrieval-augmented generation for legal research
- document_search: Searching legal documents
- citation_tools: Legal citation validation
- document_generation: Generating legal documents

### Knowledge Spaces
- indian_legal_system: Structure and functioning of Indian legal system
- indian_statutes: Comprehensive knowledge of Indian acts and laws
- indian_regulations: Regulatory frameworks in Indian jurisdictions
- indian_case_law: Precedential case law from Indian courts
- legal_terminology: Legal terminology and concepts

### Reasoning Strategies
- legal_authority_verification: Systematic approach to verifying legal authority
- compliance_risk_assessment: Systematic approach to assessing compliance risks

## Positions

### 1. Legal Analyst
- **ID**: legal_analyst
- **Type**: Specialist
- **Seniority**: Mid
- **Criticality**: High
- **Headcount**: 1-10 (recommended: 3)
- **Key Skills**: legal_research, document_analysis, contract_analysis, legal_writing, citation_validation
- **Key Tools**: legal_document_parser, rag_retrieval, document_search, citation_tools, document_generation
- **Key Knowledge**: indian_legal_system, indian_statutes, indian_case_law, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: research, analysis
- **Output**: legal_analysis

### 2. Contract Specialist
- **ID**: contract_specialist
- **Type**: Specialist
- **Seniority**: Mid
- **Criticality**: High
- **Headcount**: 1-8 (recommended: 2)
- **Key Skills**: contract_analysis, legal_writing, document_analysis, compliance_analysis
- **Key Tools**: legal_document_parser, document_generation, document_search
- **Key Knowledge**: indian_statutes, indian_regulations, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: drafting, review
- **Output**: contract_document

### 3. Compliance Analyst
- **ID**: compliance_analyst
- **Type**: Specialist
- **Seniority**: Mid
- **Criticality**: High
- **Headcount**: 1-5 (recommended: 2)
- **Key Skills**: compliance_analysis, document_analysis, legal_research, legal_writing
- **Key Tools**: document_search, rag_retrieval, legal_document_parser, document_generation
- **Key Knowledge**: indian_regulations, indian_statutes, indian_legal_system, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: compliance_check, risk_assessment
- **Output**: compliance_report

### 4. Legal Researcher
- **ID**: legal_researcher
- **Type**: Specialist
- **Seniority**: Mid
- **Criticality**: High
- **Headcount**: 1-8 (recommended: 2)
- **Key Skills**: legal_research, document_analysis, citation_validation
- **Key Tools**: rag_retrieval, document_search, citation_tools, legal_document_parser
- **Key Knowledge**: indian_case_law, indian_statutes, indian_legal_system, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: research, verification
- **Output**: legal_research_report

### 5. Legal Reviewer
- **ID**: legal_reviewer
- **Type**: Specialist
- **Seniority**: Senior
- **Criticality**: High
- **Headcount**: 1-5 (recommended: 2)
- **Key Skills**: document_analysis, legal_writing, citation_validation, contract_analysis, compliance_analysis
- **Key Tools**: legal_document_parser, citation_tools, document_search, rag_retrieval
- **Key Knowledge**: indian_case_law, indian_statutes, indian_regulations, indian_legal_system, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: review, quality_assurance
- **Output**: legal_review_report

### 6. Senior Lawyer
- **ID**: senior_lawyer
- **Type**: Leadership
- **Seniority**: Senior
- **Criticality**: High
- **Headcount**: 1-3 (recommended: 1)
- **Key Skills**: legal_research, document_analysis, contract_analysis, compliance_analysis, legal_writing, citation_validation
- **Key Tools**: legal_document_parser, rag_retrieval, document_search, citation_tools, document_generation
- **Key Knowledge**: indian_legal_system, indian_statutes, indian_regulations, indian_case_law, legal_terminology
- **Pipeline**: legal_pipeline
- **Stages**: strategy, advisory, final_review
- **Output**: legal_opinion, strategy_document

## Team Members

### Individual Members
1. **Raghav Mehta** (emp_leg_analyst_001) - Legal Analyst
2. **Isha Verma** (emp_leg_contract_001) - Contract Specialist
3. **Aditi Sharma** (emp_leg_researcher_001) - Legal Researcher
4. **Armaan Kapoor** (emp_leg_reviewer_001) - Legal Reviewer
5. **Vikram Singh** (emp_leg_senior_001) - Senior Lawyer
6. **Priya Nair** (emp_leg_compliance_001) - Compliance Analyst

### Baseline Members
- legal_analyst_baseline
- contract_specialist_baseline
- compliance_analyst_baseline
- legal_researcher_baseline
- legal_reviewer_baseline
- senior_lawyer_baseline

## Pipelines

### 1. Main Legal Pipeline (legal_pipeline)
- **Input**: standard_task
- **Output**: legal_output
- **Stages**:
  1. research - Legal Research
  2. analysis - Document Analysis
  3. authority_verification - Authority Verification
  4. drafting - Legal Drafting
  5. compliance_check - Compliance Check
  6. review - Legal Review
  7. final_approval - Final Approval

### 2. Legal Research Pipeline (legal_research_pipeline)
- **Input**: standard_task
- **Output**: legal_research_report
- **Stages**:
  1. legal_research - Legal Research
  2. authority_verification - Authority Verification
  3. analysis - Analysis
  4. drafting - Drafting
  5. review - Review

### 3. Contract Review Pipeline (contract_review_pipeline)
- **Input**: contract_document
- **Output**: contract_review_report
- **Stages**:
  1. contract_analysis - Contract Analysis
  2. risk_assessment - Risk Assessment
  3. compliance_check - Compliance Check
  4. legal_review - Legal Review
  5. recommendations - Recommendations

### 4. Compliance Pipeline (compliance_pipeline)
- **Input**: compliance_request
- **Output**: compliance_report
- **Stages**:
  1. requirement_identification - Requirement Identification
  2. risk_assessment - Risk Assessment
  3. gap_analysis - Gap Analysis
  4. mitigation_planning - Mitigation Planning
  5. report_generation - Report Generation

## Team Structure
```
Legal Team
├── Senior Lawyer (Leadership)
├── Legal Analyst (Specialist)
├── Contract Specialist (Specialist)
├── Compliance Analyst (Specialist)
├── Legal Researcher (Specialist)
└── Legal Reviewer (Specialist)
```

## Jurisdiction Focus
The legal team is specifically configured for Indian legal jurisdiction, with expertise in:
- Indian legal system structure
- Indian statutes and legislation
- Indian regulatory frameworks
- Indian case law and precedents
- Indian legal terminology