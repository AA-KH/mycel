def get_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "compile_executive_blueprint",
                "description": "Compiles the final executive blueprint JSON from all team member reports. The structure MUST strictly match the pixel-art UI format requirements.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "network_map": {
                            "type": "object",
                            "properties": {
                                "tier_1_suppliers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "allocation_pct": {"type": "integer"},
                                            "lead_time_days": {"type": "integer"},
                                            "landed_cost": {"type": "number"},
                                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                                        },
                                        "required": ["name", "allocation_pct", "lead_time_days", "risk_level"]
                                    }
                                },
                                "manufacturing": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "capacity_units": {"type": "integer"},
                                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                                        },
                                        "required": ["name", "capacity_units", "risk_level"]
                                    }
                                },
                                "warehousing": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "safety_stock_days": {"type": "integer"},
                                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                                        },
                                        "required": ["name", "safety_stock_days", "risk_level"]
                                    }
                                },
                                "distribution": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "details": {"type": "string"},
                                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                                        },
                                        "required": ["name", "details", "risk_level"]
                                    }
                                },
                                "customers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "details": {"type": "string"},
                                            "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}
                                        },
                                        "required": ["name", "details", "risk_level"]
                                    }
                                }
                            }
                        },
                        "council_decision": {
                            "type": "object",
                            "properties": {
                                "verdict": {"type": "string"},
                                "allocation": {"type": "string"},
                                "reason": {"type": "string"},
                                "trade_off": {"type": "string"},
                                "resilience": {"type": "string"}
                            },
                            "required": ["verdict", "allocation", "reason", "trade_off", "resilience"]
                        },
                        "implementation_rollout": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "phase": {"type": "integer"},
                                    "task": {"type": "string"},
                                    "status": {"type": "string", "enum": ["READY NOW", "REQUIRES VALIDATION", "REQUIRES NEGOTIATION", "REQUIRES USER ACTION"]}
                                },
                                "required": ["phase", "task", "status"]
                            }
                        }
                    },
                    "required": ["network_map", "council_decision", "implementation_rollout"]
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
