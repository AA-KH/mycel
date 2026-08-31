# TOS 3: Team Common Tools System

## What is a Tool?
A **Tool** in Mycel is an actionable capability defined inside the Global Tool System (`backend/tools/`). It answers the question: *"What action can be performed?"* (e.g. `web.search`, `filesystem.write`). 
It represents a concrete execution path (via an Executor and Provider), and it defines strict input/output schemas.

## What is a Team Tool?
A **Team Tool** represents an action that is generally available to an operational domain (Team). When a Team is assigned a Tool (via a `TeamToolAssignment`), it defines the sandbox of actions that the organization makes available to that team.

## Why Skills and Tools are Different
- **Skill**: Defines *intent and expectations* ("What capability does the team possess?"). E.g., `web_research`.
- **Tool**: Defines *concrete actions* ("What action can the team perform?"). E.g., `web.search`, `browser.open`.

A single Skill may use multiple Tools. A Tool may support multiple Skills. They are many-to-many conceptual entities and are deliberately decoupled in the Mycel architecture.

## How Team Tool Assignments Work
A `TeamToolAssignment` is a lightweight pointer mapping a `team_id` to a global `tool_id`.
This architecture ensures that the global Tool Definition (schemas, execution metadata) is NEVER duplicated inside the Team definition.

## Shared Tools
Because the global `ToolRegistry` remains the authoritative source of truth, a single Tool (like `web.search`) can be shared across multiple Teams simply by creating multiple `TeamToolAssignment` records.

## Importance
Assignments carry an `importance` enum (`CORE`, `SUPPORTING`, `OPTIONAL`). This describes how central the tool is to the Team's operations.

## Required Flag
A `required` boolean flag indicates if the tool is strictly necessary for the Team to function. This is distinct from importance; an important tool might still be optional.

## Access Mode
Assignments include an `access_mode` (`READ`, `WRITE`, `EXECUTE`, `FULL`). While the global Tool System defines the technical execution, the `AccessMode` provides metadata for future security policy resolution (e.g. ensuring a Team is only granted `READ` access to a filesystem tool, even if the tool supports `WRITE`).
