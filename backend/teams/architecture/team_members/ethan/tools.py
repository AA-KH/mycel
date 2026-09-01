def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "run_chaos_simulation",
                "description": "Simulates random catastrophic failures (e.g., region outage, DDoS) on the architecture.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "architecture_components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of core components (e.g., 'API Gateway', 'Database', 'Message Queue')"
                        },
                        "failure_scenario": {
                            "type": "string",
                            "enum": ["region_outage", "ddos_attack", "database_corruption", "message_queue_overload"]
                        }
                    },
                    "required": ["architecture_components", "failure_scenario"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "detect_anti_patterns",
                "description": "Scans the proposed architecture for dangerous anti-patterns.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "architecture_description": {"type": "string"}
                    },
                    "required": ["architecture_description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "validate_compliance",
                "description": "Audits the design against strict enterprise standards (SOC2, GDPR).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "handles_pii": {"type": "boolean"},
                        "data_encrypted_at_rest": {"type": "boolean"},
                        "has_audit_logs": {"type": "boolean"}
                    },
                    "required": ["handles_pii", "data_encrypted_at_rest", "has_audit_logs"]
                }
            }
        }
    ]
