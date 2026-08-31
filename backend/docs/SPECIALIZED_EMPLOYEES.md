# Specialized Employee System

Phase 8 introduces the canonical identity of AI agents within the Mycel platform. Instead of dynamically assembling agents from generic roles, Mycel now employs **Specialized Employees**.

## Core Concepts

### 1. Stable Identity (`employee_id`)
Every employee has a permanent, stable `employee_id`. This ID is used across the system to track tasks, artifacts, and performance. Changing an employee's skills, tools, or reasoning profile does not alter their identity.

### 2. Capabilities
An employee's capabilities are explicitly defined:
- **Skills**: Domain-specific proficiencies (e.g., `python_programming: 95`).
- **Tools**: The explicit set of tools the employee is allowed to use (Least Privilege).
- **Outputs**: The artifact types the employee can generate (e.g., `source_code`, `research_report`).

### 3. Reasoning Profile
Employees are assigned a `reasoning_profile_id` (e.g., `research_verify`, `code_test`) which maps to a specific `ReasoningStrategy` in the execution engine.

### 4. Lifecycle & Availability
- **Status**: `DRAFT`, `ACTIVE`, `INACTIVE`, `SUSPENDED`, `RETIRED`.
- **Availability**: `AVAILABLE`, `BUSY`, `OFFLINE`.

## 5. Employee Catalogue

### Aarav Mehta
- **Employee ID**: `emp_aarav_mehta`
- **Department**: `dept_research`
- **Team**: `team_market_intelligence`
- **Position**: `pos_research_specialist`
- **Specialization**: Competitive Intelligence
- **Skills**: Market Analysis (95), Data Synthesis (90), Trend Forecasting (85)
- **Reasoning Profile**: `research_verify`
- **Tools**: `web_search`, `read_url`, `create_artifact`
- **Expected Outputs**: `research_report`, `competitive_analysis`, `market_report`
- **Status**: ACTIVE

### Kabir Sharma
- **Employee ID**: `emp_kabir_sharma`
- **Department**: `dept_engineering`
- **Team**: `team_backend`
- **Position**: `pos_backend_engineer`
- **Specialization**: API Architecture
- **Skills**: Python (96), FastAPI (95), API Design (94), Database Design (89), Testing (91)
- **Reasoning Profile**: `code_test`
- **Tools**: `filesystem.read`, `filesystem.write`, `python.execute`, `github.read`
- **Expected Outputs**: `source_code`, `api`, `test_suite`, `documentation`
- **Status**: ACTIVE

### Riya Sharma
- **Employee ID**: `emp_riya_sharma`
- **Department**: `dept_creative`
- **Team**: `team_creative_production`
- **Position**: `pos_video_producer`
- **Specialization**: Promotional Video
- **Skills**: Video Editing (96), Storytelling (94), Visual Design (88), Marketing Content (82)
- **Reasoning Profile**: `creative_review`
- **Tools**: `image.generate`, `video.generate`, `audio.generate`, `ffmpeg`, `cloudinary.upload`
- **Expected Outputs**: `video`, `thumbnail`, `audio`
- **Status**: ACTIVE

