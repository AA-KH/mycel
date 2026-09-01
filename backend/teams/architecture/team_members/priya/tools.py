def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_gantt_chart",
                "description": "Generates a Mermaid.js Gantt chart showing the exact timeline, parallel tasks, and dependencies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "section": {"type": "string", "description": "e.g., 'Backend API', 'Frontend UI'"},
                                    "task_name": {"type": "string"},
                                    "duration": {"type": "string", "description": "e.g., '2w', '5d'"},
                                    "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Names of tasks this depends on"}
                                },
                                "required": ["section", "task_name", "duration"]
                            }
                        }
                    },
                    "required": ["title", "tasks"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "estimate_sprint_velocity",
                "description": "Calculates how many sprints a feature will take based on complexity, team size, and backend/frontend split.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "feature_name": {"type": "string"},
                        "complexity": {"type": "string", "enum": ["low", "medium", "high", "extreme"]},
                        "engineers_assigned": {"type": "integer"}
                    },
                    "required": ["feature_name", "complexity", "engineers_assigned"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "map_technical_dependencies",
                "description": "Generates a JSON dependency tree proving which services must be built first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "critical_path": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "parallel_tracks": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "required": ["critical_path", "parallel_tracks"]
                }
            }
        }
    ]
