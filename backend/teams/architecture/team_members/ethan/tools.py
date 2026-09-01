def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "generate_mermaid_graph",
                "description": "Generates Mermaid.js syntax for architecture diagrams to map out the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "graph_type": {
                            "type": "string",
                            "enum": ["flowchart", "sequence"],
                            "description": "Type of diagram."
                        },
                        "elements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "target": {"type": "string"},
                                    "label": {"type": "string"},
                                    "from": {"type": "string"},
                                    "to": {"type": "string"},
                                    "message": {"type": "string"}
                                }
                            },
                            "description": "List of relationships or sequence events."
                        },
                        "title": {
                            "type": "string"
                        }
                    },
                    "required": ["graph_type", "elements"]
                }
            }
        }
    ]
