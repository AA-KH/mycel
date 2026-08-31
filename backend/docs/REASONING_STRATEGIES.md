# Reasoning Strategies

A **Reasoning Strategy** dictates *how* an employee approaches a task. While all strategies implement the same base interface (`understand`, `decompose_and_plan`, `decide_next_action`, `critique`, `verify`), they use different psychological approaches and system prompts.

## Available Strategies

### 1. General Problem Solving (`GeneralReasoningStrategy`)
- **Focus**: Step-by-step linear progression.
- **Best for**: Routine administrative tasks, data entry, simple querying.

### 2. Research & Verify (`ResearchVerifyStrategy`)
- **Focus**: Gathering evidence, detecting conflicts, synthesizing reliable reports.
- **Best for**: Researchers, Analysts, Strategists.
- **Key Behavior**: Actively seeks multiple sources before jumping to conclusions.

### 3. Code & Test (`CodeTestStrategy`)
- **Focus**: Inspecting environment, implementing, running automated tests, and revising based on logs.
- **Best for**: Software Engineers, QA, DevOps.
- **Key Behavior**: Will not finalize a task without passing verification tests.

### 4. Creative Review (`CreativeReviewStrategy`)
- **Focus**: Scripting, storyboarding, asset generation, and brand alignment.
- **Best for**: Designers, Content Creators, Marketing.
- **Key Behavior**: Prioritizes emotional impact and brand consistency over strict logical deduction.
