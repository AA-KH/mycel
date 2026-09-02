import json
from teams.architecture.base import ArchitectureBaseAgent
from .profile import NAME, ROLE
from .prompt import SYSTEM_PROMPT
from .tools import get_tools

class EthanAgent(ArchitectureBaseAgent):
    def __init__(self, session_id: str = None):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools(),
            session_id=session_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "run_chaos_simulation":
            components = arguments.get("architecture_components", [])
            scenario = arguments.get("failure_scenario", "")
            
            # Simulated chaos logic
            survives = True
            vulnerabilities = []
            
            if scenario == "region_outage":
                if not any("multi-region" in c.lower() or "global" in c.lower() for c in components):
                    survives = False
                    vulnerabilities.append("Single region dependency detected.")
            elif scenario == "ddos_attack":
                if not any("gateway" in c.lower() or "waf" in c.lower() or "cloudflare" in c.lower() for c in components):
                    survives = False
                    vulnerabilities.append("No WAF or API Gateway detected to absorb DDoS.")
            elif scenario == "database_corruption":
                if not any("backup" in c.lower() or "replica" in c.lower() for c in components):
                    survives = False
                    vulnerabilities.append("No database replication strategy detected.")
                    
            return json.dumps({
                "scenario": scenario,
                "components_tested": components,
                "survived": survives,
                "vulnerabilities": vulnerabilities,
                "resilience_score": 100 if survives else max(0, 100 - (len(vulnerabilities) * 40))
            })
            
        elif function_name == "detect_anti_patterns":
            desc = arguments.get("architecture_description", "").lower()
            anti_patterns = []
            
            if "shared database" in desc and "microservices" in desc:
                anti_patterns.append("Distributed Monolith (Microservices sharing a single DB)")
            if "synchronous" in desc and "chain" in desc:
                anti_patterns.append("Service Chain of Death (Too many synchronous calls)")
            
            return json.dumps({
                "anti_patterns_detected": anti_patterns,
                "status": "Warning" if anti_patterns else "Clean",
                "recommendation": "Decouple services using event streams." if anti_patterns else "Architecture looks clean."
            })
            
        elif function_name == "validate_compliance":
            handles_pii = arguments.get("handles_pii", False)
            encrypted = arguments.get("data_encrypted_at_rest", False)
            audit_logs = arguments.get("has_audit_logs", False)
            
            violations = []
            if handles_pii and not encrypted:
                violations.append("GDPR/SOC2 Violation: PII data must be encrypted at rest.")
            if handles_pii and not audit_logs:
                violations.append("SOC2 Violation: Missing audit logs for PII access.")
                
            return json.dumps({
                "compliance_status": "FAILED" if violations else "PASSED",
                "violations": violations,
                "confidence_penalty": len(violations) * 20
            })
            
        else:
            return await super().execute_tool(function_name, arguments)
