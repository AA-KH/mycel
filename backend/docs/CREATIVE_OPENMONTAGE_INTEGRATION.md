# OpenMontage Integration Report — Mycel Creative Designer

## What Was Inspected

- **Repository:** `https://github.com/calesthio/OpenMontage`
- **Type:** Open-source agentic video production system
- **Files Reviewed:** `README.md`, `AGENT_GUIDE.md`

---

## What Was Selected (Concepts Only)

| OpenMontage Concept | What Was Adapted | Where in Mycel |
|---|---|---|
| Pipeline stage sequencing (`research → proposal → assets → edit → compose`) | 7-stage Design Asset Creation pipeline | `teams/creative/pipelines/design_asset_creation.py` |
| Iterative review loop (bounded generations) | `asset_generation` stage capped at 3 rounds | Design pipeline |
| Scene/layout planning before generation | `storyboard_layout` pipeline stage | Design pipeline |
| "Taste direction" / style dial concept | `visual_direction` pipeline stage (lock style before generating) | Design pipeline |
| Quality gate with human approval for hero deliverables | `design_review` stage + existing `quality/` system | Mycel quality system |

---

## What Was Rejected

| OpenMontage Concept | Reason Rejected |
|---|---|
| Remotion / HyperFrames rendering engines | Video-specific. Not applicable to design asset creation. |
| Backlot board server (`python -m backlot`) | OpenMontage-specific project dashboard, incompatible with Mycel. |
| `lib/checkpoint.py` | OpenMontage-specific state persistence. Mycel has its own execution system. |
| `tools/cost_tracker.py` | Out of scope. Mycel does not yet have budget governance. |
| `pipeline_defs/*.yaml` manifest format | Mycel uses Python pipeline model (`TeamPipeline`), not YAML. |
| Composition runtimes (Templated vs Atelier code) | Video composition concept. Not applicable to static design assets. |
| Entire `projects/` workspace convention | Video project directories. Mycel uses the Artifact system. |
| Music library system | Audio/video specific. Not applicable to design tools. |
| `tools/tool_registry` provider menu system | Mycel has its own ToolRegistry. |

---

## What Was NOT Copied

- No OpenMontage Python files were copied.
- No OpenMontage package (`openmontage_sdk` etc.) was installed.
- No git clone, submodule, or vendor directory was created.
- No OpenMontage directory structure was replicated.

---

## Runtime Dependency Status

**OpenMontage is NOT a runtime dependency of Mycel.**

Mycel runs completely independently of the OpenMontage repository. Removing or making OpenMontage unavailable has zero effect on Mycel.

---

## Attribution

The workflow concept (staged pipeline from brief to delivery) is a common software engineering pattern. The specific stage names and ordering in `design_asset_creation.py` were inspired by OpenMontage's production philosophy, not copied from its code. No license obligations arise from conceptual inspiration.
