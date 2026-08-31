# Reasoning Security

Security in the Reasoning domain focuses on maintaining the purity of the methodology and preventing state leakage.

## No Chain-of-Thought Persistence
The `TeamReasoningProfile` is explicitly forbidden from storing private chain-of-thought, hidden LLM deliberation traces, or unstructured execution dumps. It acts purely as a configuration schema.

## Profile Access
Agents and normal runtime processes are granted **READ-ONLY** access to the `TeamReasoningProfile` via the `TeamReasoningResolver`. 

## Profile Mutation
Only authorized organization or team administrators may mutate the Team Reasoning Philosophy. Agents cannot modify their team's philosophy mid-execution.

## Model Independence
The philosophy is model-agnostic. It does not contain `OpenAI`, `Groq`, or `Anthropic` specific prompt formats. The `ReasoningEngine` acts as the translation layer between the abstract Philosophy and the concrete `LLMProvider`.
