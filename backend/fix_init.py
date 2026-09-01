import os
import glob
import re

base_files = [
    r"d:\Projects\mycel\backend\teams\intelligence\base.py",
    r"d:\Projects\mycel\backend\teams\network\base.py",
    r"d:\Projects\mycel\backend\teams\resilience\base.py",
    r"d:\Projects\mycel\backend\teams\council\base.py",
]

for base_file in base_files:
    with open(base_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list):
    content = re.sub(
        r'def __init__\(self, name: str, role: str, system_prompt: str, user_id: str, tools: list\):',
        r'def __init__(self, name: str, role: str, system_prompt: str, user_id: str, tools: list, session_id: str = None):',
        content
    )
    # Update super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id)
    content = re.sub(
        r'super\(\)\.__init__\(name=name, role=role, system_prompt=system_prompt, user_id=user_id\)',
        r'super().__init__(name=name, role=role, system_prompt=system_prompt, user_id=user_id, session_id=session_id)',
        content
    )
    
    with open(base_file, "w", encoding="utf-8") as f:
        f.write(content)

# Now agent files
agent_files = glob.glob(r"d:\Projects\mycel\backend\teams\*\team_members\*\agent.py")

for agent_file in agent_files:
    with open(agent_file, "r", encoding="utf-8") as f:
        content = f.read()

    # For intelligence agents: def __init__(self, task_id: str, user_id: str = "system"):
    # Change to: def __init__(self, task_id: str = "default", user_id: str = "system", session_id: str = None):
    content = re.sub(
        r'def __init__\(self, task_id: str, user_id: str = "system"\):',
        r'def __init__(self, task_id: str = "default", user_id: str = "system", session_id: str = None):',
        content
    )
    
    # For others: def __init__(self, task_id: str = "default"):
    # Change to: def __init__(self, task_id: str = "default", session_id: str = None):
    content = re.sub(
        r'def __init__\(self, task_id: str = "default"\):',
        r'def __init__(self, task_id: str = "default", session_id: str = None):',
        content
    )
    
    # Also update super().__init__ calls. We need to add session_id=session_id to the arguments.
    if 'session_id=session_id' not in content:
        # Find super().__init__( up to the closing parenthesis
        pattern = r'(super\(\)\.__init__\([\s\S]*?)(?=\s*\))'
        def replacer(match):
            text = match.group(1)
            # Add a comma if there isn't one at the end of the arguments
            if not text.rstrip().endswith(','):
                text += ','
            text += '\n            session_id=session_id'
            return text
            
        content = re.sub(pattern, replacer, content, count=1)
    
    with open(agent_file, "w", encoding="utf-8") as f:
        f.write(content)

print("Updated all base files and agent files!")
