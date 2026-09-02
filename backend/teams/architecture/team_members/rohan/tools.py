def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "design_supply_chain_network",
                "description": "Designs a structured supply chain logistics pipeline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin_country": {"type": "string"},
                        "destination_country": {"type": "string"},
                        "tier_1_suppliers": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "transit_nodes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "E.g., Ports, Warehouses, Distribution Centers"
                        },
                        "estimated_lead_time_days": {"type": "integer"}
                    },
                    "required": ["origin_country", "destination_country", "tier_1_suppliers", "transit_nodes", "estimated_lead_time_days"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "simulate_bottleneck",
                "description": "Simulates the impact of a critical node failing in the supply chain.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "failed_node": {"type": "string"},
                        "downtime_days": {"type": "integer"},
                        "has_backup_node": {"type": "boolean"}
                    },
                    "required": ["failed_node", "downtime_days", "has_backup_node"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_mermaid_graph",
                "description": "Generates a flowchart representing the supply chain topology and geography.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mermaid_syntax": {
                            "type": "string",
                            "description": "Raw Mermaid.js syntax (e.g., 'flowchart TD\n  A-->B'). Do not include markdown codeblocks."
                        },
                        "title": {"type": "string"}
                    },
                    "required": ["mermaid_syntax", "title"]
                }
            }
        }
    ]
