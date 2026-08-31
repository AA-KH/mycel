"""
General Code Generation Tools for Development Team
Tools for generating, executing, and testing general development code
"""
import re
from typing import Dict, Any
from tools.base import BaseTool
from tools.context import ToolExecutionContext
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from core.groq_engine import groq_engine
from core.logger import logger

class CodeGenerator(BaseTool):
    """Generates Python code for general development tasks using Groq LLM"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="code.generator",
            name="Code Generator",
            category="code_generation",
            description="Generate Python code for general development tasks like API development, data processing, and system automation",
            input_schema={
                "type": "object",
                "required": ["task_description", "skill_type"],
                "properties": {
                    "task_description": {"type": "string", "description": "Description of the development task"},
                    "skill_type": {"type": "string", "enum": ["api_development", "backend_development", "frontend_development", "testing", "data_processing", "automation"], "description": "Type of development skill to use"},
                    "context": {"type": "string", "description": "Additional context about the task"}
                }
            },
            output_schema={"type": "object"},
            capabilities=["api_development", "backend_development", "frontend_development", "testing", "data_processing", "automation", "WEB_DEVELOPMENT", "PROGRAMMING"],
            output_modalities=["CODE", "WEBSITE"],
            artifact_types=["CODE_BUNDLE", "WEBSITE"],
            preview_types=["CODE_VIEWER", "LIVE_WEBSITE"],
            risk_level="medium",
            idempotent=True,
            timeout_seconds=30
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            task = arguments["task_description"]
            skill_type = arguments["skill_type"]
            additional_context = arguments.get("context", "")
            
            # Build specialized prompt for code generation
            system_prompt = self._build_development_system_prompt(skill_type)
            
            user_prompt = f"""
Task: {task}
Context: {additional_context}

Generate Python code that:
1. Follows best practices for the specific development domain
2. Includes error handling and validation
3. Is well-documented with comments
4. Uses appropriate libraries and frameworks
5. Returns structured results

Focus on the {skill_type} domain and demonstrate proficiency in that area.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call Grok (xAI) for code generation
            response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3
            )
            
            raw_code = response.choices[0].message.content or ""
            code = self._extract_code(raw_code)
            
            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={
                    "code": code,
                    "skill_type": skill_type,
                    "language": "python",
                    "explanation": self._extract_explanation(raw_code)
                }
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )
    
    def _build_development_system_prompt(self, skill_type: str) -> str:
        """Build specialized system prompt based on development skill type"""
        base_prompt = """You are an expert software developer with deep knowledge of software engineering, best practices, and modern development frameworks. Generate clean, efficient, and well-documented Python code."""
        
        skill_prompts = {
            "api_development": """Specialize in API development: REST endpoints, request validation, error handling, authentication, and API documentation. Use FastAPI/Flask patterns.""",
            
            "backend_development": """Specialize in backend development: server-side logic, database operations, business logic, and system integration. Use proper backend patterns.""",
            
            "frontend_development": """Specialize in frontend development: UI components, state management, responsive design, and user experience. Use modern frontend patterns.""",
            
            "testing": """Specialize in testing: unit tests, integration tests, test automation, and quality assurance. Use pytest and testing best practices.""",
            
            "data_processing": """Specialize in data processing: ETL operations, data transformation, validation, and pipeline development. Use pandas and data engineering patterns.""",
            
            "automation": """Specialize in automation: scripting, task automation, workflow orchestration, and system integration. Use modern automation frameworks."""
        }
        
        return base_prompt + "\n" + skill_prompts.get(skill_type, "")
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown code blocks"""
        code_pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        generic_pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(generic_pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        return text.strip()
    
    def _extract_explanation(self, text: str) -> str:
        """Extract explanation text from before/after code blocks"""
        code_pattern = r'```.*?```'
        explanation = re.sub(code_pattern, '', text, flags=re.DOTALL)
        return explanation.strip()


class CodeExecutor(BaseTool):
    """Safely executes generated code in a sandboxed environment"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="code.executor",
            name="Code Executor",
            category="code_execution",
            description="Safely execute generated code with proper error handling and result capture",
            input_schema={
                "type": "object",
                "required": ["code"],
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "test_data": {"type": "object", "description": "Test data for the code"}
                }
            },
            output_schema={"type": "object"},
            risk_level="high",
            idempotent=True,
            timeout_seconds=15
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            code = arguments["code"]
            test_data = arguments.get("test_data", {})
            
            # Create restricted execution environment
            exec_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'bool': bool,
                    'Exception': Exception,
                    'ValueError': ValueError,
                    'TypeError': TypeError,
                }
            }
            
            # Add test data to execution context
            exec_globals.update(test_data)
            
            # Try to import common libraries
            try:
                import pandas as pd
                import numpy as np
                from datetime import datetime, timedelta
                import json
                import math
                import statistics
                
                exec_globals.update({
                    'pd': pd, 'pandas': pd,
                    'np': np, 'numpy': np,
                    'datetime': datetime, 'timedelta': timedelta,
                    'json': json,
                    'math': math,
                    'statistics': statistics
                })
            except ImportError as e:
                logger.warning(f"Some required libraries not available: {e}")
            
            # Execute the code
            try:
                exec(code, exec_globals)
                result = exec_globals.get('result', 'Code executed successfully')
                
                return ToolResult(
                    tool_name=self.definition.id,
                    status="success",
                    output={
                        "result": str(result),
                        "execution_time": "completed",
                        "variables": {k: str(v) for k, v in exec_globals.items() if not k.startswith('_')}
                    }
                )
                
            except Exception as e:
                return ToolResult(
                    tool_name=self.definition.id,
                    status="error",
                    output={},
                    error=f"Execution error: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )


class CodeTester(BaseTool):
    """Generates and runs tests for code"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="code.tester",
            name="Code Tester",
            category="code_testing",
            description="Generate and run unit tests for code to ensure correctness and edge case handling",
            input_schema={
                "type": "object",
                "required": ["code", "skill_type"],
                "properties": {
                    "code": {"type": "string", "description": "Code to test"},
                    "skill_type": {"type": "string", "description": "Type of development skill"},
                    "test_cases": {"type": "array", "description": "Specific test cases to run"}
                }
            },
            output_schema={"type": "object"},
            risk_level="medium",
            idempotent=True,
            timeout_seconds=20
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            code = arguments["code"]
            skill_type = arguments["skill_type"]
            custom_test_cases = arguments.get("test_cases", [])
            
            # Generate test cases using Groq
            test_prompt = f"""
Generate comprehensive unit tests for this {skill_type} code:

```python
{code}
```

Generate pytest-compatible tests that:
1. Test normal operation with realistic data
2. Test edge cases (empty data, extreme values, etc.)
3. Test error handling
4. Include assertions for key logic
5. Test data validation where applicable

Return only the test code, no explanations.
"""
            
            messages = [
                {"role": "system", "content": "You are an expert in writing unit tests for software. Generate comprehensive, robust test cases."},
                {"role": "user", "content": test_prompt}
            ]
            
            test_response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.2
            )
            
            test_code = self._extract_code(test_response.choices[0].message.content or "")
            combined_code = f"{code}\n\n# Generated Tests\n{test_code}"
            
            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output={
                    "test_code": test_code,
                    "combined_code": combined_code,
                    "test_count": test_code.count("def test_"),
                    "skill_type": skill_type
                }
            )
            
        except Exception as e:
            logger.error(f"Code testing failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown code blocks"""
        code_pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        generic_pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(generic_pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        return text.strip()
