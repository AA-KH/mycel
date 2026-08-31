"""
Finance Development API Routes
Endpoints for interacting with the Finance Developer Agent
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from organization.schemas import APIResponse
from teams.finance.agents.finance_developer_agent import FinanceDeveloperAgent
from tools.registry import registry

# Import and register finance tools from the correct location
from teams.finance.common.tools.individual.finance_code_generator import FinanceAnalyst, FinanceReporter

router = APIRouter()

# Register finance tools
try:
    registry.register(FinanceAnalyst())
    registry.register(FinanceReporter())
except Exception as e:
    print(f"Warning: Could not register finance tools: {e}")

@router.post("/finance/develop", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def develop_finance_solution(
    task_description: str,
    skill_type: str,
    context: str = "",
    test_requirements: Optional[List[str]] = None
):
    """
    Generate, test, and execute finance code for a given task.
    
    Parameters:
    - task_description: Description of the finance task to accomplish
    - skill_type: Type of finance skill (accounting, financial_modeling, budgeting, data_analysis, forecasting)
    - context: Additional context about the task
    - test_requirements: Specific test cases to include
    """
    try:
        # Validate skill type
        valid_skills = ["accounting", "financial_modeling", "budgeting", "data_analysis", "forecasting", "cost_analysis"]
        if skill_type not in valid_skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skill_type. Must be one of: {', '.join(valid_skills)}"
            )
        
        # Initialize agent
        agent = FinanceDeveloperAgent()
        
        # Develop solution
        result = await agent.develop_finance_solution(
            task_description=task_description,
            skill_type=skill_type,
            context=context,
            test_requirements=test_requirements or []
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Finance development failed")
            )
        
        return APIResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Finance development error: {str(e)}"
        )

@router.post("/finance/refine", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def refine_finance_code(
    original_code: str,
    feedback: str,
    skill_type: str
):
    """
    Refine existing finance code based on feedback.
    
    Parameters:
    - original_code: The original code to refine
    - feedback: Specific feedback for improvements
    - skill_type: Type of finance skill
    """
    try:
        agent = FinanceDeveloperAgent()
        
        result = await agent.refine_code(
            original_code=original_code,
            feedback=feedback,
            skill_type=skill_type
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Code refinement failed")
            )
        
        return APIResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code refinement error: {str(e)}"
        )

@router.get("/finance/skills", response_model=APIResponse)
async def get_finance_skills():
    """Get available finance skill types for code generation"""
    skills = {
        "accounting": {
            "description": "Accounting tasks like reconciliation, financial statements, compliance",
            "examples": ["Bank reconciliation", "Financial statement generation", "Compliance checks"]
        },
        "financial_modeling": {
            "description": "Financial modeling, DCF analysis, valuation models",
            "examples": ["DCF valuation", "Sensitivity analysis", "Monte Carlo simulation"]
        },
        "budgeting": {
            "description": "Budget management, variance analysis, cost optimization",
            "examples": ["Budget allocation", "Variance analysis", "Cost optimization"]
        },
        "data_analysis": {
            "description": "Financial data analysis, trend identification, ratio calculations",
            "examples": ["Trend analysis", "Financial ratios", "Anomaly detection"]
        },
        "forecasting": {
            "description": "Revenue forecasting, time series analysis, predictions",
            "examples": ["Revenue forecasting", "Cash flow prediction", "Demand planning"]
        },
        "cost_analysis": {
            "description": "Cost analysis, margin calculation, break-even analysis",
            "examples": ["Cost structure analysis", "Margin optimization", "Break-even analysis"]
        }
    }
    
    return APIResponse(data=skills)

@router.get("/finance/tools", response_model=APIResponse)
async def get_finance_tools():
    """Get available finance development tools"""
    tools = {
        "finance.code_generator": {
            "description": "Generate Python code for finance tasks",
            "category": "code_generation"
        },
        "finance.code_executor": {
            "description": "Safely execute generated finance code",
            "category": "code_execution"
        },
        "finance.code_tester": {
            "description": "Generate and run tests for finance code",
            "category": "code_testing"
        },
        "spreadsheet.processing": {
            "description": "Process spreadsheet data for finance operations",
            "category": "data_processing"
        },
        "financial.calculator": {
            "description": "Perform financial calculations and computations",
            "category": "calculation"
        }
    }
    
    return APIResponse(data=tools)
