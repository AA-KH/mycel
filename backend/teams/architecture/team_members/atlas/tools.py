def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "compile_executive_blueprint",
                "description": "Compiles the final executive blueprint JSON from all team member reports.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "final_decision": {"type": "string", "enum": ["APPROVED", "REJECTED", "APPROVED_WITH_CONDITIONS"]},
                        "key_risks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Synthesized list of all critical risks (from Ethan & Rohan)."
                        },
                        "estimated_timeline": {"type": "string", "description": "Synthesized from Priya's sprint calculation."},
                        "executive_summary": {"type": "string"}
                    },
                    "required": ["final_decision", "key_risks", "estimated_timeline", "executive_summary"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_total_risk_matrix",
                "description": "Calculates the total health/risk score of the system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "security_vulnerabilities_count": {"type": "integer"},
                        "supply_chain_bottlenecks_count": {"type": "integer"},
                        "critical_path_dependencies_count": {"type": "integer"}
                    },
                    "required": ["security_vulnerabilities_count", "supply_chain_bottlenecks_count", "critical_path_dependencies_count"]
                }
            }
        }
    ]
