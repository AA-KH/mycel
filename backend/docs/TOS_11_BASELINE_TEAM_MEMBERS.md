# Phase TOS 11: Baseline Team Members

## What is a Baseline Member?
A **Baseline Team Member** is a canonical workforce template that serves as the theoretical minimum competent worker for a specific Team Position. It embodies the intersection of what the Team universally demands and what the Position specifically requires.

## Why Baseline Member Exists
While a **Position** establishes abstract *requirements* (e.g. "We need someone who knows Python"), a **Baseline Member** establishes the *actual baseline identity* that fulfills those requirements (e.g. "A worker with Python skill level 70 and access to git/github"). 
It acts as the anchor point between the abstract structural needs of the company and the highly specialized, chaotic nature of actual human/AI employees. 

## Position vs Baseline Member vs Actual Member
1. **Position:** "What does the Team need?"
2. **Baseline Member:** "What is the standard, generic worker who fills this need?"
3. **Actual Member:** "Who is the specific, unique worker currently sitting in the seat?"

## Capability Inheritance
The Baseline Member does not reinvent capabilities. It systematically inherits from its parent structures:
- **Team Common Skills + Position Skills -> Baseline Skills**
- **Team Common Tools + Position Tools -> Baseline Tools**
- **Team Knowledge + Position Knowledge -> Baseline Knowledge**
- **Team Reasoning + Position Reasoning -> Baseline Reasoning**

## Responsibilities
The Baseline Member formally declares responsibility for specific execution pipelines, stages, and output contracts derived from its parent Position. Crucially, the Baseline Member *declares* these, but does not *execute* them. Execution remains the strict domain of the Agent Runtime.

## Future Smart Hiring Relationship
TOS 11 explicitly prepares the architecture for Smart Hiring. In the future hiring pipeline, the system will look at an empty Position, instantiate its Baseline Member, and then compare that Baseline against thousands of Candidate Members (Employees) in the global catalogue. The candidate whose *Individual Specialization* best satisfies the delta against the Baseline will be selected.
