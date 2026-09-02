import asyncio
import importlib
import json
from typing import List, Dict, Any
from core.logger import logger
from core.events import event_publisher
from teams.architecture.team_members.atlas.agent import AtlasAgent

class MasterOrchestrator:
    """
    Dynamically executes any hired agents across all teams in parallel,
    then feeds their output into the Master Orchestrator (Atlas) for synthesis.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id

    async def run_project_analysis(self, master_prompt: str, hired_personnel: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"🚀 [GLOBAL ORCHESTRATOR] Initiating 4-Phase Execution Pipeline for {self.session_id}")
        
        # Categorize agents into phases
        phase1_agents = [] # Research (Intelligence, Council, Network)
        phase2_agents = [] # Drafting (Architecture planners)
        phase3_agents = [] # Validation (Resilience, Chaos)
        atlas_person = None # Synthesis
        
        for person in hired_personnel:
            agent_id = person.get("agent_id", "")
            team = person.get("team", "").upper()
            name = person.get("name", "")
            
            if agent_id == "architecture_atlas":
                atlas_person = person
            elif team in ["INTELLIGENCE", "COUNCIL", "NETWORK"]:
                phase1_agents.append(person)
            elif team == "RESILIENCE" or name.lower() == "ethan":
                phase3_agents.append(person)
            else:
                # Default to Phase 2 (Architecture planners)
                phase2_agents.append(person)
                
        # To accumulate contextual history for the next phase
        accumulated_context = f"INITIAL PROJECT PROMPT:\n{master_prompt}\n"
        raw_reports = {}
        
        def truncate_report(report: str, max_chars=800) -> str:
            if not isinstance(report, str):
                report = str(report)
            if len(report) > max_chars:
                return report[:max_chars] + "...[TRUNCATED to save context]"
            return report
        
        # --- PHASE 1: Research & Discovery ---
        if phase1_agents:
            logger.info("🟢 [PHASE 1] Running Research & Discovery (Intelligence, Council, Network)...")
            p1_results = await self._run_phase(phase1_agents, accumulated_context)
            accumulated_context += "\n--- PHASE 1 (RESEARCH) REPORTS ---\n"
            for name, report in p1_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] REPORT:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 2: Drafting ---
        if phase2_agents:
            logger.info("🟡 [PHASE 2] Running Architecture Drafting (Planners)...")
            p2_prompt = accumulated_context + "\nBased on the above intelligence and requirements, draft the optimal supply chain architecture."
            p2_results = await self._run_phase(phase2_agents, p2_prompt)
            accumulated_context += "\n--- PHASE 2 (DRAFTING) REPORTS ---\n"
            for name, report in p2_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] DRAFT:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 3: Validation & Red-Teaming ---
        if phase3_agents:
            logger.info("🔴 [PHASE 3] Running Validation & Resilience (Chaos, Stress Testers)...")
            p3_prompt = accumulated_context + "\nCritique, attack, and validate the drafted architecture above. Identify single points of failure."
            p3_results = await self._run_phase(phase3_agents, p3_prompt)
            accumulated_context += "\n--- PHASE 3 (VALIDATION) REPORTS ---\n"
            for name, report in p3_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] CRITIQUE:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 4: Master Synthesis (Atlas) ---
        logger.info("🔵 [PHASE 4] Atlas synthesizing global reports...")
        
        atlas_prompt = f"""
The Global Task Force has completed its multi-phase analysis. Here is the entire contextual history:
{accumulated_context}

Synthesize these reports. Resolve conflicts. You MUST factor in ALL Intelligence, Network, Resilience, and Architectural constraints provided above.
You MUST output your final synthesis as a strict JSON object matching this schema exactly:

CRITICAL RULES:
1. Every node's "stage" field MUST exactly equal the "id" of its parent stage.
2. Every node "id" must be unique across ALL stages (e.g., "sup-a", "mfg-main", "wh-central").
3. "risk" must be one of: "low", "medium", or "high" — nothing else.
4. Include as many real nodes per stage as the analysis warrants (1 to 6 per stage). Be dynamic.
5. Output ONLY the raw JSON — no markdown fences, no commentary.

EXAMPLE of correct structure (yours must follow this exact shape with real data):
{{
  "stages": [
    {{
      "id": "suppliers",
      "label": "Tier-1 Suppliers",
      "owner": "Rohan",
      "question": "Who feeds the network?",
      "nodes": [
        {{
          "id": "sup-a",
          "stage": "suppliers",
          "name": "Supplier A",
          "share": "60%",
          "risk": "medium",
          "location": "Germany",
          "function": "Primary source — lowest landed cost, carries the base volume.",
          "flowLabel": "60% · 21d",
          "meta": ["Primary — lowest landed cost", "Lead time 21 days"],
          "detail": [{{"label": "Allocation", "value": "60% of annual volume"}}],
          "fallback": "Supplier B absorbs 40% on outage > 72h."
        }}
      ]
    }},
    {{
      "id": "manufacturing",
      "label": "Manufacturing",
      "owner": "Kabir",
      "question": "Where is value added?",
      "nodes": [
        {{
          "id": "mfg-main",
          "stage": "manufacturing",
          "name": "Primary Plant",
          "share": null,
          "risk": "high",
          "location": "India · West",
          "function": "Core production hub, capacity 140k units/yr.",
          "flowLabel": "140k units/yr",
          "meta": ["Capacity 140k units/yr", "ISO 9001 certified"],
          "detail": [{{"label": "Capacity", "value": "140k units/yr"}}],
          "fallback": "Shift 30% to contract manufacturer within 2 weeks."
        }}
      ]
    }}
  ],
  "decision": {{
    "verdict": "APPROVED — resilient dual-source network",
    "allocation": "Supplier A 60% · Supplier B 25% · Supplier C 15%",
    "reason": "Dual-source mitigates single-country dependency",
    "tradeoff": "Slightly higher cost vs single-source, offset by resilience",
    "resilience": "All critical nodes have documented fallback paths"
  }},
  "rollout": [
    {{"phase": "Phase 1", "action": "Qualify Supplier B to 25% share", "status": "Ready now"}},
    {{"phase": "Phase 2", "action": "Commission Regional Buffer warehouse", "status": "Q2 2025"}}
  ]
}}

Now generate the REAL output based on the actual analysis above. Use real supplier names, locations, percentages, and specifics from the expert reports — not placeholder text.
"""
        
        await event_publisher.publish(self.session_id, "start", {"agent": "Atlas", "task": "Synthesizing executive blueprint from all teams"})
        await event_publisher.publish(self.session_id, "log", {
            "level": "action",
            "text": f"Atlas → synthesize_blueprint(): consolidating {len(raw_reports)} expert reports into the executive architecture.",
        })
        
        # Bypass Agent loop to avoid tool hallucination and enforce JSON output
        from core.gemini_engine import engine_manager as gemini_manager
        atlas_json: Dict[str, Any] = {}
        atlas_error: str | None = None
        atlas_raw = ""
        
        try:
            # The blueprint JSON (stages -> nodes -> meta/detail, decision, rollout) is
            # several thousand tokens. The engine default of 512 tokens truncated the
            # output mid-JSON, so parsing always failed and the UI fell back to mock data.
            response = await gemini_manager.chat_completion(
                model="gemini-flash-latest",
                messages=[
                    {"role": "system", "content": "You are Atlas, the Master Orchestrator. Output ONLY valid JSON — no markdown fences, no commentary."},
                    {"role": "user", "content": atlas_prompt}
                ],
                temperature=0.2,
                max_tokens=8192,
            )
            atlas_raw = response.choices[0].message.content or ""
            atlas_json = self._parse_atlas_json(atlas_raw)
            
            if atlas_json is None:
                # One repair attempt: ask the model to return the same content as valid JSON.
                logger.warning("Atlas returned malformed JSON — attempting a repair pass.")
                repair = await gemini_manager.chat_completion(
                    model="gemini-flash-latest",
                    messages=[
                        {"role": "system", "content": "You fix malformed JSON. Output ONLY the corrected, complete JSON object. No commentary."},
                        {"role": "user", "content": f"Repair this JSON so it is valid and complete (close any unterminated arrays/objects):\n\n{atlas_raw}"}
                    ],
                    temperature=0.0,
                    max_tokens=8192,
                )
                repaired_raw = repair.choices[0].message.content or ""
                atlas_json = self._parse_atlas_json(repaired_raw)
                if atlas_json is not None:
                    atlas_raw = repaired_raw
                    
            if atlas_json is None:
                atlas_error = "Atlas did not return valid JSON"
                
        except Exception as e:
            logger.error(f"Atlas LLM synthesis failed: {str(e)}")
            atlas_error = f"Atlas LLM synthesis failed: {str(e)}"
            
        if atlas_error is None:
            atlas_json = self._normalize_atlas_output(atlas_json)
            if not atlas_json.get("stages"):
                atlas_error = "Atlas returned JSON without any stages"
                
        if atlas_error is not None:
            logger.error(f"[ATLAS] {atlas_error}. Raw head: {atlas_raw[:300]!r}")
            atlas_json = {"error": atlas_error, "raw": atlas_raw}
            await event_publisher.publish(self.session_id, "log", {
                "level": "warn",
                "text": f"Atlas synthesis failed — {atlas_error}. Blueprint tab is showing sample data until a re-run succeeds.",
            })
        else:
            await self._publish_atlas_summary(atlas_json)
            
        await event_publisher.publish(self.session_id, "finish", {"agent": "Atlas"})
            
        final_report = {
            "expert_reports": raw_reports,
            "atlas_executive": atlas_json
        }
        
        return final_report

    # ------------------------------------------------------------------ #
    # Atlas output handling                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_atlas_json(text: str) -> Dict[str, Any] | None:
        """Extract and parse the JSON object from an LLM reply. Returns None on failure."""
        if not text:
            return None
        out = text.strip()
        if "```json" in out:
            out = out.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in out:
            parts = out.split("```")
            if len(parts) >= 2:
                out = parts[1].strip()
        start, end = out.find("{"), out.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        out = out[start:end + 1]
        try:
            parsed = json.loads(out)
        except Exception:
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _normalize_atlas_output(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coerce Atlas' JSON into the exact shape the Blueprint UI renders:
        stages[].nodes[] with valid risk / stage / meta / detail fields,
        plus decision + rollout objects.
        """
        valid_risk = {"low", "medium", "high"}
        stages_in = data.get("stages") or []
        stages_out = []
        seen_ids: set[str] = set()
        
        def slug(value: Any, fallback: str) -> str:
            s = str(value or "").strip().lower()
            s = "".join(ch if ch.isalnum() else "-" for ch in s).strip("-")
            return s or fallback
        
        for s_idx, stage in enumerate(stages_in):
            if not isinstance(stage, dict):
                continue
            stage_id = slug(stage.get("id") or stage.get("label"), f"stage-{s_idx + 1}")
            base_stage_id = stage_id
            n = 2
            while stage_id in seen_ids:
                stage_id = f"{base_stage_id}-{n}"
                n += 1
            seen_ids.add(stage_id)
            
            nodes_out = []
            for n_idx, node in enumerate(stage.get("nodes") or []):
                if not isinstance(node, dict):
                    continue
                node_id = slug(node.get("id") or node.get("name"), f"{stage_id}-node-{n_idx + 1}")
                base_node_id = node_id
                n = 2
                while node_id in seen_ids:
                    node_id = f"{base_node_id}-{n}"
                    n += 1
                seen_ids.add(node_id)
                
                risk = str(node.get("risk") or "").strip().lower()
                meta = node.get("meta") or []
                detail = node.get("detail") or []
                
                nodes_out.append({
                    "id": node_id,
                    "stage": stage_id,
                    "name": str(node.get("name") or f"Node {n_idx + 1}"),
                    "share": node.get("share") if node.get("share") not in ("", "null", None) else None,
                    "risk": risk if risk in valid_risk else None,
                    "location": node.get("location") or "",
                    "function": node.get("function") or "",
                    "flowLabel": node.get("flowLabel") or node.get("flow_label") or None,
                    "flowsTo": node.get("flowsTo") if isinstance(node.get("flowsTo"), list) else None,
                    "meta": [str(m) for m in meta if m] if isinstance(meta, list) else [str(meta)],
                    "detail": [
                        {"label": str(d.get("label", "")), "value": str(d.get("value", ""))}
                        for d in detail if isinstance(d, dict)
                    ],
                    "fallback": node.get("fallback") or "",
                })
                
            if not nodes_out:
                continue
            stages_out.append({
                "id": stage_id,
                "label": str(stage.get("label") or stage_id.replace("-", " ").title()),
                "owner": str(stage.get("owner") or "Atlas"),
                "question": str(stage.get("question") or ""),
                "nodes": nodes_out,
            })
            
        # Resolve flowsTo references to ids that actually exist; drop the rest.
        for stage in stages_out:
            for node in stage["nodes"]:
                if node["flowsTo"]:
                    node["flowsTo"] = [t for t in node["flowsTo"] if t in seen_ids] or None
                if node["flowsTo"] is None:
                    node.pop("flowsTo")
                    
        decision_in = data.get("decision") if isinstance(data.get("decision"), dict) else {}
        decision = {
            "verdict": str(decision_in.get("verdict") or "Pending"),
            "allocation": str(decision_in.get("allocation") or "—"),
            "reason": str(decision_in.get("reason") or "—"),
            "tradeoff": str(decision_in.get("tradeoff") or "—"),
            "resilience": str(decision_in.get("resilience") or "—"),
        }
        
        rollout = []
        for r_idx, phase in enumerate(data.get("rollout") or []):
            if not isinstance(phase, dict):
                continue
            rollout.append({
                "phase": str(phase.get("phase") or f"Phase {r_idx + 1}"),
                "action": str(phase.get("action") or ""),
                "status": str(phase.get("status") or "Planned"),
            })
            
        normalized = dict(data)
        normalized.update({"stages": stages_out, "decision": decision, "rollout": rollout})
        return normalized

    async def _publish_atlas_summary(self, atlas_json: Dict[str, Any]) -> None:
        """Surface Atlas' actual output in the orchestrator feed."""
        stages = atlas_json.get("stages", [])
        node_count = sum(len(s.get("nodes", [])) for s in stages)
        decision = atlas_json.get("decision", {})
        rollout = atlas_json.get("rollout", [])
        
        publish = event_publisher.publish
        await publish(self.session_id, "log", {
            "level": "success",
            "text": f"Atlas blueprint compiled — {len(stages)} stages · {node_count} nodes · {len(rollout)} rollout phases.",
        })
        for i, stage in enumerate(stages):
            names = ", ".join(n.get("name", "") for n in stage.get("nodes", []))
            await publish(self.session_id, "log", {
                "level": "info",
                "text": f"Stage {i + 1:02d} · {stage.get('label')} ({stage.get('owner')}): {names}",
            })
        if decision.get("verdict"):
            await publish(self.session_id, "log", {"level": "success", "text": f"Atlas verdict: {decision['verdict']}"})
        if decision.get("allocation") and decision["allocation"] != "—":
            await publish(self.session_id, "log", {"level": "info", "text": f"Allocation: {decision['allocation']}"})
        if decision.get("reason") and decision["reason"] != "—":
            await publish(self.session_id, "log", {"level": "info", "text": f"Rationale: {decision['reason']}"})
        if decision.get("tradeoff") and decision["tradeoff"] != "—":
            await publish(self.session_id, "log", {"level": "info", "text": f"Trade-off: {decision['tradeoff']}"})
        if decision.get("resilience") and decision["resilience"] != "—":
            await publish(self.session_id, "log", {"level": "info", "text": f"Resilience: {decision['resilience']}"})
        for phase in rollout:
            await publish(self.session_id, "log", {
                "level": "action",
                "text": f"Rollout · {phase.get('phase')}: {phase.get('action')} [{phase.get('status')}]",
            })

    async def _run_phase(self, personnel: List[Dict[str, Any]], phase_prompt: str) -> Dict[str, str]:
        tasks = []
        agent_names = []
        
        for person in personnel:
            agent_id = person.get("agent_id")
            try:
                parts = agent_id.split("_")
                team_name = parts[0].lower()
                member_name = parts[1].lower()
                class_name = f"{member_name.capitalize()}Agent"
                module_path = f"teams.{team_name}.team_members.{member_name}.agent"
                
                module = importlib.import_module(module_path)
                AgentClass = getattr(module, class_name)
                
                agent_instance = AgentClass(session_id=self.session_id)
                agent_name = person.get("name", member_name.capitalize())
                agent_role = person.get("role", "Specialist")
                
                agent_names.append({"name": agent_name, "role": agent_role})
                tasks.append(self._run_agent_task(agent_instance, agent_name, agent_role, phase_prompt))
                
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        phase_reports = {}
        for i, res in enumerate(results):
            name = agent_names[i]["name"]
            phase_reports[name] = res if not isinstance(res, Exception) else f"FAILED: {str(res)}"
            
        return phase_reports

    async def _run_agent_task(self, agent_instance, name, role, prompt):
        await event_publisher.publish(self.session_id, "start", {"agent": name, "task": f"Analyzing {role} constraints"})
        try:
            # Some base agents expect (task_description), some (task) - mostly task_description
            res = await agent_instance.run_task(prompt)
        except Exception as e:
            res = str(e)
        await event_publisher.publish(self.session_id, "finish", {"agent": name})
        return res
