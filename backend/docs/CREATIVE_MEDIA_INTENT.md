# Creative Media Intent Resolution

Mycel orchestrates Arjun's capabilities dynamically based on user intent, avoiding hardcoded monolithic stages.

## Process
1. **User Request**: The user asks for a promotional video, a technical explainer, or a marketing asset.
2. **Intent Resolution**: The orchestrator matches the intent against the `PIPELINE_REGISTRY`. 
   - Requests needing deep technical explanation route to `technical_explainer`.
   - Requests needing quick promotional content route to `hybrid_video`.
3. **Capability Mapping**: Once a pipeline is selected, it executes utilizing the `CreativeReviewStrategy` in a loop. The agent selects from its allowed `COMMON_TOOLS`.

## Example
If a user requests: *"Explain binary search visually."*
1. **Pipeline**: `technical_explainer`
2. **Action 1**: Generates Manim Python code representing Binary Search.
3. **Action 2**: Calls `creative.technical_animation.render` with the code.
4. **Action 3**: Retrieves `artifact_url` and finalizes the asset.
