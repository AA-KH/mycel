Set-Location -Path "d:\Projects\agent-virtual-office\backend"

# 1. Organization
Rename-Item -Path "company" -NewName "organization" -ErrorAction Continue

# 2. Workforce
New-Item -ItemType Directory -Force -Path "workforce"
Move-Item -Path "modules\employees" -Destination "workforce\employees" -ErrorAction Continue

# 3. Hiring
Move-Item -Path "modules\hiring" -Destination "hiring" -ErrorAction Continue

# 4. Tasks
Move-Item -Path "modules\tasks" -Destination "tasks" -ErrorAction Continue

# 5. Auth and Realtime (Moving to api/v1/routes)
Move-Item -Path "modules\auth" -Destination "api\v1\routes\auth" -ErrorAction Continue
Move-Item -Path "modules\realtime" -Destination "api\v1\routes\realtime" -ErrorAction Continue

# 6. API Router
Move-Item -Path "modules\api_router.py" -Destination "api\v1\routes\data.py" -ErrorAction Continue

# 7. Remove empty modules dir
# Wait, modules still has __init__.py and README.md. Let's remove them.
Remove-Item -Path "modules\__init__.py" -ErrorAction Continue
Remove-Item -Path "modules\README.md" -ErrorAction Continue
Remove-Item -Path "modules" -Recurse -Force -ErrorAction Continue
