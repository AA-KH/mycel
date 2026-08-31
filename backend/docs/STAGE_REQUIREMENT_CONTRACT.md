# Stage Requirement Contract

This contract serves as the foundation for the future **Smart Hiring Engine**. 
It declaratively states what a particular chunk of work requires to be executed properly.

## Components
1. **Skills**: (`StageSkillRequirement`) References a specific `skill_id` (e.g., `video_editing`) and an optional proficiency minimum.
2. **Tools**: (`StageToolRequirement`) References specific `tool_id`s (e.g., `web.search`, `ffmpeg.render`) that the worker must be granted access to.
3. **Knowledge**: (`StageKnowledgeRequirement`) Declares if external knowledge retrieval is `NO_KNOWLEDGE`, `OPTIONAL_KNOWLEDGE`, or `REQUIRED_KNOWLEDGE`, including optional domain restrictions.
4. **Reasoning**: (`StageReasoningRequirement`) References an explicit Reasoning Strategy from TOS 5 that the Agent must utilize during internal deliberation.
5. **Outputs**: (`StageOutputContract`) The exact output formats and artifacts the Stage demands.

## Crucial Principle
This contract dictates requirements. It **DOES NOT**:
- Assign an actual Employee or Agent.
- Directly invoke a Tool.
- Execute an LLM call.

The Smart Hiring engine will later read this contract and find an Employee whose personal capabilities match the defined requirements perfectly.
