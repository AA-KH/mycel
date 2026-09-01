def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "query_available_agents",
                "description": "Queries the database for a list of all available AI agents, their roles, and their skills.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "hire_team",
                "description": "Submits the final list of agents hired for this project along with their specific project mandates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hired_personnel": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "agent_id": {"type": "string", "description": "The unique ID from the database"},
                                    "name": {"type": "string"},
                                    "role": {"type": "string"},
                                    "team": {"type": "string", "description": "e.g., ARCHITECTURE, COUNCIL"},
                                    "badge": {"type": "string", "description": "Generate a retro badge ID, e.g., MYC-020-ETH"},
                                    "mandate": {"type": "string", "description": "A short, sharp sentence on exactly what this agent must do for this specific project. (e.g., 'Attack the blueprint. Sign off only if it holds.')"},
                                    "status": {"type": "string", "enum": ["GREEN", "AMBER", "RED"]}
                                },
                                "required": ["agent_id", "name", "role", "team", "badge", "mandate", "status"]
                            }
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation of why this specific task force was assembled."
                        }
                    },
                    "required": ["hired_personnel", "reasoning"]
                }
            }
        }
    ]
