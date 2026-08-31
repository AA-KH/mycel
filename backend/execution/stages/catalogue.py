from execution.stages.models import (
    StageDefinition, StageDefinitionStatus, StageCategory,
    StageInputContract, StageOutputContract, StageValidationContract,
    StageRequirementContract, StageSkillRequirement, StageToolRequirement,
    StageKnowledgeRequirement, KnowledgeRequirementType, StageReasoningRequirement
)

def get_base_stage_definitions() -> list[StageDefinition]:
    """Returns a catalogue of foundational reusable Stage Definitions."""
    
    return [
        # ---------------------------------------------------------
        # RESEARCH
        # ---------------------------------------------------------
        StageDefinition(
            stage_definition_id="understand_requirement",
            name="understand_requirement",
            display_name="Understand Requirement",
            description="Analyzes the incoming task to establish a clear requirement.",
            purpose="Understand and decompose the initial task into a structured requirement.",
            domain="global",
            category=StageCategory.ANALYSIS,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="task_description", required_fields=["task"]),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="requirements_analysis", required=True)],
                output_contract_id="structured_requirement"
            )
        ),
        StageDefinition(
            stage_definition_id="web_research",
            name="web_research",
            display_name="Web Research",
            description="Collects relevant information from the web.",
            purpose="Search external sources to gather evidence for a claim or topic.",
            domain="global",
            category=StageCategory.RESEARCH,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="structured_requirement", required_fields=["query"]),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="web_research", required=True)],
                tools=[StageToolRequirement(tool_id="web.search", required=True)],
                output_contract_id="source_collection"
            )
        ),
        StageDefinition(
            stage_definition_id="source_verification",
            name="source_verification",
            display_name="Source Verification",
            description="Cross-references claims with reliable sources.",
            purpose="Verify important claims against reliable evidence.",
            domain="global",
            category=StageCategory.VERIFICATION,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="source_collection"),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="source_validation", required=True)],
                reasoning=StageReasoningRequirement(reasoning_strategy_id="research_verify", required=True),
                output_contract_id="verified_evidence"
            ),
            validation_contract=StageValidationContract(verification_required=True)
        ),
        StageDefinition(
            stage_definition_id="research_synthesis",
            name="research_synthesis",
            display_name="Research Synthesis",
            description="Synthesizes findings into a final report.",
            purpose="Transform verified evidence into a structured research result.",
            domain="global",
            category=StageCategory.ANALYSIS,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="verified_evidence"),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="evidence_analysis", required=True)],
                output_contract_id="research_report"
            )
        ),
        
        # ---------------------------------------------------------
        # ENGINEERING
        # ---------------------------------------------------------
        StageDefinition(
            stage_definition_id="code_implementation",
            name="code_implementation",
            display_name="Code Implementation",
            description="Writes code based on requirements.",
            purpose="Implement software features or fixes.",
            domain="engineering",
            category=StageCategory.CODING,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="structured_requirement"),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="software_development", required=True)],
                tools=[StageToolRequirement(tool_id="filesystem.write", required=True)],
                output_contract_id="code_package"
            )
        ),
        StageDefinition(
            stage_definition_id="test_execution",
            name="test_execution",
            display_name="Test Execution",
            description="Runs automated tests.",
            purpose="Verify code correctness via tests.",
            domain="engineering",
            category=StageCategory.TESTING,
            status=StageDefinitionStatus.ACTIVE,
            input_contract=StageInputContract(input_type="code_package"),
            requirement_contract=StageRequirementContract(
                skills=[StageSkillRequirement(skill_id="testing", required=True)],
                tools=[StageToolRequirement(tool_id="test.runner", required=True)],
                output_contract_id="test_result"
            )
        )
    ]
