def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "validate_json_schema",
                "description": "Validates a sample data payload against a proposed JSON schema.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "object",
                            "description": "The JSON schema definition."
                        },
                        "sample_data": {
                            "type": "object",
                            "description": "The sample data payload to validate against the schema."
                        }
                    },
                    "required": ["schema", "sample_data"]
                }
            }
        },
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
                            }
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
