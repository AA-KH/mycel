from typing import Dict, Any
from .snapshot import ExecutionSnapshot

class InstructionBuilder:
    """
    Generates structured system prompts dynamically from Employee definitions.
    Prevents hardcoding "You are a researcher" and relies on the Employee's
    identity, skills, and tools.
    """
    
    @staticmethod
    def build_system_prompt(snapshot: ExecutionSnapshot, task: Dict[str, Any]) -> str:
        prompt_parts = []
        
        # 1. Identity
        prompt_parts.append(f"You are {snapshot.title} at Mycel.")
        prompt_parts.append(f"Role Summary: {snapshot.identity_summary}")
        prompt_parts.append(f"Personality: {snapshot.personality}")
        prompt_parts.append(f"Communication Style: {snapshot.communication_style}")
        prompt_parts.append("")
        
        # 2. Skills
        if snapshot.skills:
            prompt_parts.append("Your Capabilities & Skills:")
            for skill, proficiency in snapshot.skills.items():
                prompt_parts.append(f"- {skill}: {proficiency}/100")
            prompt_parts.append("")
            
        # 3. Tools
        if snapshot.tools:
            prompt_parts.append("Available Tools:")
            prompt_parts.append("You have access to tools that you can request to use during your planning phase.")
            for tool in snapshot.tools:
                prompt_parts.append(f"- {tool}")
            prompt_parts.append("")
            
        # 4. Rules & Instructions
        prompt_parts.append("Execution Rules:")
        prompt_parts.append("1. Analyze the task and structure your output in valid JSON.")
        prompt_parts.append("2. DO NOT output hidden chain-of-thought. Use the structured fields.")
        prompt_parts.append("3. If you need to use a tool, specify the tool name and arguments.")
        prompt_parts.append("4. Adhere to your communication style and role limitations.")
        prompt_parts.append("5. The expected output format is defined in the task.")
        prompt_parts.append("")
        
        # 5. Task context
        prompt_parts.append("Current Task:")
        prompt_parts.append(f"Title: {task.get('title', 'Untitled')}")
        prompt_parts.append(f"Description: {task.get('description', '')}")
        if 'expected_output' in task:
            prompt_parts.append(f"Expected Output: {task.get('expected_output')}")
        if 'constraints' in task:
            prompt_parts.append(f"Constraints: {task.get('constraints')}")
            
        return "\n".join(prompt_parts)
