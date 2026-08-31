"""
Meera — Research Analyst

Turns a vague business/user objective into a rigorous research plan.
Decomposes large questions into specific, actionable research questions
with search strategies and acceptance criteria.

Meera is analytical, not merely summarizing. She identifies:
- What information is actually needed (explicit + implicit)
- What source types are required
- Dependencies between questions
- Potential biases and gaps
- Acceptance criteria for evidence sufficiency
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from core.groq_engine import engine_manager
from teams.research.models import (
    ResearchPlan, ResearchQuestion, SearchStrategy,
    ResearchRequestType, ResearchQuestionPriority,
    SourceType, ResearchTrace
)

logger = logging.getLogger(__name__)

# Meera's system prompt — focused on analytical decomposition
MEERA_SYSTEM_PROMPT = """You are Meera, the Research Analyst at Mycel.

Your role is to transform a research request into a rigorous, actionable research plan.

You are analytical, meticulous, and thorough. You think like an investigative analyst, not a search engine.

When given a research request, you must:
1. Understand the user's ACTUAL intent (not just literal words)
2. Identify ALL information requirements (explicit AND implicit)
3. Decompose into specific, answerable research questions
4. For each question, specify search queries and source types needed
5. Identify dependencies between questions
6. Set acceptance criteria for evidence sufficiency

RULES:
- Be specific. "Find information about X" is NOT a good research question.
- Good research questions are: "What are X's pricing tiers?", "What do independent reviews say about X's reliability?", "What technologies does X use?"
- Think about what a human researcher would actually investigate
- Consider: official sources, documentation, reviews, forums, news, comparisons
- Identify time-sensitive questions that need current information
- Identify questions requiring primary vs secondary sources
- Flag potential biases and information gaps

You MUST respond in valid JSON matching the schema provided."""

# Research type detection prompt
CLASSIFY_PROMPT = """Classify this research request into one of these types:
- competitor_analysis: Investigating specific competitors
- market_research: Understanding a market/industry  
- technical_research: Technical investigation (frameworks, APIs, etc.)
- product_research: Investigating specific products
- pricing_research: Comparing pricing/costs
- technology_evaluation: Evaluating technology options
- open_source_evaluation: Evaluating open source tools
- comparative_analysis: Comparing multiple entities
- company_research: Investigating a company
- general: Other

Return ONLY the type string, nothing else."""


class MeeraResearchAnalyst:
    """
    Meera — Research Analyst Agent
    
    Responsibilities:
    - Understand research request
    - Classify research type
    - Decompose into research questions
    - Generate search strategies
    - Create research plan with acceptance criteria
    """
    
    def __init__(self, trace: Optional[ResearchTrace] = None):
        self.name = "Meera"
        self.role = "Research Analyst"
        self.trace = trace or ResearchTrace()
        self._engine = engine_manager.get_engine("research")
    
    async def create_research_plan(self, request: str) -> ResearchPlan:
        """
        Main entry point: transform a raw request into a structured research plan.
        """
        self.trace.log(
            agent=self.name,
            action="received_request",
            details=f"Analyzing research request: {request[:200]}",
            input_summary=request[:200]
        )
        
        # 1. Classify the research type
        research_type = await self._classify_request(request)
        
        # 2. Generate the research plan via LLM
        plan = await self._generate_plan(request, research_type)
        
        self.trace.log(
            agent=self.name,
            action="created_research_plan",
            details=f"Created plan with {len(plan.questions)} questions, type={research_type}",
            output_summary=f"Plan: {plan.interpreted_objective[:200]}"
        )
        
        return plan
    
    async def _classify_request(self, request: str) -> ResearchRequestType:
        """Classify the type of research request."""
        try:
            messages = [
                {"role": "system", "content": CLASSIFY_PROMPT},
                {"role": "user", "content": request}
            ]
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.1,
                max_tokens=50
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip().lower()
            
            # Try to match to enum
            for rt in ResearchRequestType:
                if rt.value in raw:
                    return rt
            return ResearchRequestType.GENERAL
        except Exception as e:
            logger.error(f"[Meera] Classification failed: {e}")
            return ResearchRequestType.GENERAL
    
    async def _generate_plan(self, request: str, research_type: ResearchRequestType) -> ResearchPlan:
        """Generate a structured research plan using LLM."""
        
        plan_generation_prompt = f"""Analyze this research request and create a comprehensive research plan.

RESEARCH REQUEST:
{request}

RESEARCH TYPE: {research_type.value}

Return a JSON object with this EXACT structure:
{{
    "interpreted_objective": "Clear statement of what this research aims to discover",
    "scope_description": "What is in scope and out of scope",
    "key_entities": ["entity1", "entity2"],
    "questions": [
        {{
            "text": "Specific research question",
            "priority": "critical|high|medium|low",
            "category": "pricing|features|technical|competitive|sentiment|market|general",
            "requires_current_info": true/false,
            "requires_primary_sources": true/false,
            "requires_quantitative_data": true/false,
            "minimum_source_count": 2,
            "search_queries": ["query 1", "query 2", "query 3"],
            "source_types_needed": ["official_website", "review_site", "forum_post"],
            "depends_on": []
        }}
    ],
    "acceptance_criteria": ["criterion 1", "criterion 2"],
    "stopping_criteria": ["All critical questions answered", "At least 2 independent sources per major claim"]
}}

IMPORTANT:
- Generate at LEAST 5 specific questions for any non-trivial request
- Each question must have 2-4 search queries
- Questions should cover: facts, opinions/reviews, comparisons, current state, limitations
- Include questions about potential BIASES or GAPS in available information
- For competitor analysis: pricing, features, target users, reviews, technical stack, limitations, recent changes
- For technical research: documentation, examples, performance, alternatives, community, limitations
- Be THOROUGH — a lazy plan produces lazy research"""

        try:
            messages = [
                {"role": "system", "content": MEERA_SYSTEM_PROMPT},
                {"role": "user", "content": plan_generation_prompt}
            ]
            
            response = await self._engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            
            plan_data = json.loads(json_match.group())
            
            # Build ResearchPlan from LLM output
            plan = self._parse_plan(request, research_type, plan_data)
            return plan
            
        except Exception as e:
            logger.error(f"[Meera] Plan generation failed: {e}")
            # Fallback: create a basic plan from the request
            return self._create_fallback_plan(request, research_type)
    
    def _parse_plan(self, request: str, research_type: ResearchRequestType, 
                     plan_data: Dict[str, Any]) -> ResearchPlan:
        """Parse LLM output into a ResearchPlan object."""
        questions = []
        
        for q_data in plan_data.get("questions", []):
            # Map priority string to enum
            priority_map = {
                "critical": ResearchQuestionPriority.CRITICAL,
                "high": ResearchQuestionPriority.HIGH,
                "medium": ResearchQuestionPriority.MEDIUM,
                "low": ResearchQuestionPriority.LOW,
            }
            priority = priority_map.get(
                q_data.get("priority", "medium").lower(),
                ResearchQuestionPriority.MEDIUM
            )
            
            # Map source types
            source_types = []
            for st in q_data.get("source_types_needed", []):
                try:
                    source_types.append(SourceType(st))
                except ValueError:
                    pass
            
            question = ResearchQuestion(
                text=q_data.get("text", ""),
                priority=priority,
                category=q_data.get("category", "general"),
                requires_current_info=q_data.get("requires_current_info", False),
                requires_primary_sources=q_data.get("requires_primary_sources", False),
                requires_quantitative_data=q_data.get("requires_quantitative_data", False),
                minimum_source_count=q_data.get("minimum_source_count", 2),
                search_strategy=SearchStrategy(
                    queries=q_data.get("search_queries", []),
                    source_types_needed=source_types,
                    rationale=f"Investigating: {q_data.get('text', '')[:100]}"
                ),
                depends_on=q_data.get("depends_on", [])
            )
            
            if question.text:  # Skip empty questions
                questions.append(question)
                self.trace.log(
                    agent=self.name,
                    action="created_research_question",
                    details=f"Q: {question.text[:100]}",
                    question_id=question.question_id
                )
        
        return ResearchPlan(
            original_request=request,
            interpreted_objective=plan_data.get("interpreted_objective", request),
            research_type=research_type,
            questions=questions,
            scope_description=plan_data.get("scope_description", ""),
            acceptance_criteria=plan_data.get("acceptance_criteria", []),
            stopping_criteria=plan_data.get("stopping_criteria", [
                "All critical questions have at least one supported answer",
                "Key claims verified by independent sources"
            ]),
            key_entities=plan_data.get("key_entities", []),
            created_by=self.name
        )
    
    def _create_fallback_plan(self, request: str, research_type: ResearchRequestType) -> ResearchPlan:
        """Create a basic research plan when LLM fails."""
        logger.warning("[Meera] Using fallback plan generation")
        
        # Extract potential entities from request
        words = request.split()
        entities = [w for w in words if w[0].isupper() and len(w) > 2] if words else []
        
        questions = [
            ResearchQuestion(
                text=f"What is the current state of: {request[:100]}?",
                priority=ResearchQuestionPriority.CRITICAL,
                category="general",
                search_strategy=SearchStrategy(
                    queries=[request[:100], f"{request[:50]} overview"],
                    rationale="Primary investigation"
                )
            ),
            ResearchQuestion(
                text=f"What are the key facts and data points related to: {request[:100]}?",
                priority=ResearchQuestionPriority.HIGH,
                category="general",
                search_strategy=SearchStrategy(
                    queries=[f"{request[:50]} facts data", f"{request[:50]} statistics"],
                    rationale="Factual evidence collection"
                )
            ),
            ResearchQuestion(
                text=f"What are the main opinions, reviews, and perspectives on: {request[:100]}?",
                priority=ResearchQuestionPriority.MEDIUM,
                category="sentiment",
                search_strategy=SearchStrategy(
                    queries=[f"{request[:50]} reviews opinions", f"{request[:50]} reddit"],
                    rationale="Sentiment and opinion research"
                )
            ),
        ]
        
        return ResearchPlan(
            original_request=request,
            interpreted_objective=f"Investigate: {request}",
            research_type=research_type,
            questions=questions,
            acceptance_criteria=["At least 3 questions answered with evidence"],
            stopping_criteria=["All critical questions addressed"],
            key_entities=entities[:5],
            created_by=self.name
        )
