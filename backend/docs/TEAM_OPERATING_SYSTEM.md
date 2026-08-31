# Team Operating System

## What a Team Is

A Team in Mycel is a **self-contained operational unit**. It is not just a folder, an LLM prompt, or a list of agents.

A Team knows:

| Aspect | What it knows |
|---|---|
| **WHO IT IS** | Identity, name, company, status |
| **WHAT IT CAN DO** | Common skills, tools, outputs |
| **WHAT IT KNOWS** | Knowledge spaces |
| **HOW IT REASONS** | Reasoning philosophy |
| **WHICH TOOLS** | Tool IDs available to members |
| **HOW IT WORKS** | Pipeline definitions and stages |
| **WHAT QUALITY** | Quality gate requirements |
| **WHAT IT PRODUCES** | Output contracts |
| **WHICH POSITIONS** | Available roles |
| **WHO ITS MEMBERS ARE** | Baseline workforce |
| **HOW MEMBERS INHERIT** | Capability inheritance model |
| **HOW IT ACCEPTS WORK** | Execution contracts |
| **HOW IT COLLABORATES** | Collaboration contracts |
| **HOW HEALTHY IT IS** | Readiness and health reports |

---

## What a Team Owns

```
TEAM
 │
 ├── Identity
 ├── Common Skills
 ├── Common Tools
 ├── Knowledge Spaces
 ├── Reasoning Philosophy
 ├── Pipelines
 │   └── Stages
 ├── Quality Gates
 ├── Output Contracts
 ├── Positions
 │   └── Members
 │       └── Inherited + Specialised Capabilities
 ├── Execution Contracts
 └── Collaboration Contracts
```

---

## How Teams Collaborate

Teams are autonomous. They do not directly access each other's internal state.

All inter-team work is governed by a `TeamCollaborationContract`:

```
Requesting Team
      ↓
TeamCollaborationContract
      ↓
Providing Team
      ↓
Output / ArtifactReference
      ↓
Requesting Team
```

---

## How Execution Contracts Work

An Execution Contract defines how a Team accepts a specific type of task:

```
TASK TYPE
    ↓
TEAM EXECUTION CONTRACT
    ↓
PIPELINE
    ↓
POSITIONS
    ↓
MEMBERS → AGENTS (future)
    ↓
TOOLS + KNOWLEDGE
    ↓
ARTIFACT
    ↓
QUALITY GATES
    ↓
OUTPUT
```

---

## How Members Fit Inside Teams

```
TEAM COMMON CAPABILITY
        +
POSITION REQUIREMENTS
        +
MEMBER SPECIALISATION
        =
EFFECTIVE MEMBER CAPABILITY
```

Members inherit team common capabilities. Individual specialisation is additive.

---

## How Future Agents Fit

Each member maps to an agent at runtime:

```
MEMBER
    ↓
AGENT (runtime identity)
    ↓
RUNTIME
    ↓
REASONING + TOOLS + KNOWLEDGE
    ↓
PIPELINE STAGE EXECUTION
```

The Team Operating System provides the structured identity that future runtime systems read. It does not create or run agents.
