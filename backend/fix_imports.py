import os
import re

replacements = [
    # Company -> Organization
    (r'from company\.', r'from organization.'),
    (r'import company\.', r'import organization.'),
    (r'from organization import', r'from organization import'),
    
    # Modules -> Workforce
    (r'from modules\.employees', r'from workforce.employees'),
    (r'import modules\.employees', r'import workforce.employees'),
    
    # Modules -> Hiring
    (r'from modules\.hiring', r'from hiring'),
    (r'import modules\.hiring', r'import hiring'),
    
    # Modules -> Tasks
    (r'from modules\.tasks', r'from tasks'),
    (r'import modules\.tasks', r'import tasks'),
    
    # Modules -> Auth
    (r'from modules\.auth', r'from api.v1.routes.auth'),
    (r'import modules\.auth', r'import api.v1.routes.auth'),
    
    # Modules -> Realtime
    (r'from modules\.realtime', r'from api.v1.routes.realtime'),
    (r'import modules\.realtime', r'import api.v1.routes.realtime'),
    
    # modules.api_router -> api.v1.routes.data
    (r'from api.v1.routes import data as api_router', r'from api.v1.routes import data as api_router'),
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements:
        new_content = re.sub(old, new, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated imports in {filepath}")

def main():
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                process_file(filepath)

if __name__ == "__main__":
    main()
