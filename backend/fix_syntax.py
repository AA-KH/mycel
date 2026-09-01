import glob
import re

files_to_fix = glob.glob(r"d:\Projects\mycel\backend\teams\*\team_members\*\agent.py")

for filepath in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # The issue:
    # role="General Counsel (Legal & Trade,
    #         session_id=session_id)",
    
    # We want to change it back to:
    # role="General Counsel (Legal & Trade)",
    #         session_id=session_id,
    
    # Let's use a regex that looks for:
    # role="(.*?),\s*session_id=session_id\)",
    # and replaces it with:
    # role="\1)",\n            session_id=session_id,
    
    pattern = r'(role=".*?\(),\s*session_id=session_id\)",'
    
    # Wait, the string was `role="Disruption Scenario Generator (Chaos Engineer)"`
    # and it became:
    # `role="Disruption Scenario Generator (Chaos Engineer,\n            session_id=session_id)",`
    
    # Let's write a targeted regex:
    # Find: `,\n            session_id=session_id)"`
    # Replace with: `)",\n            session_id=session_id`
    
    new_content = content.replace(',\n            session_id=session_id)",', ')",\n            session_id=session_id')
    
    if content != new_content:
        print(f"Fixed {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
