# TOS 5: Team Reasoning Philosophy

## Overview
The Team Reasoning Philosophy defines **"HOW does this Team approach problems?"**
It establishes a domain-specific methodology that guides Agents working within that Team.

## Separation of Concerns
Mycel strictly decouples reasoning from other core domains:
- **Skills**: "What capabilities does the Team possess?" (e.g. `software_development`)
- **Tools**: "What actions can the Team perform?" (e.g. `web.search`)
- **Knowledge**: "What information can the Team access?" (e.g. `Indian Legal Codes`)
- **Reasoning**: "How should the capabilities, actions, and information be combined to solve the problem?" (e.g. `plan_implement_test`)

## No Private Chain-of-Thought
A CRITICAL architectural mandate of TOS 5 is that **Reasoning Philosophy is Methodology, not Execution Trace**. 
We DO NOT store or track private chain-of-thought, prompt dumps, or hidden LLM deliberations inside the Team profile. We only store declarative rules, principles, and strategy assignments.
