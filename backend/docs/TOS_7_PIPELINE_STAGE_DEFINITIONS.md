# Phase TOS 7: Pipeline Stage Definitions

## Overview
Phase TOS 7 successfully decouples *WHAT* a stage is (`StageDefinition`) from *WHERE* it exists in a pipeline (`PipelineStage`). 

## The Concept
A `StageDefinition` is a **reusable capability specification**. It defines the inputs, the required tools, skills, reasoning profiles, and expected outputs. 
A `PipelineStage` simply references that definition via a `stage_definition_id` pointer.

This architecture enables multiple different teams and pipelines to utilize standard, vetted behaviors (e.g. `source_verification` or `code_implementation`) without duplicating configuration and contracts.

## Key Changes from TOS 6
In TOS 6, `StageRequirements` were embedded directly into the `PipelineStage`. As of TOS 7, those requirements have been extracted out into `StageRequirementContract` existing solely on the `StageDefinition`. The `TeamPipelineRegistry` now ensures that any referenced definitions actually exist and are currently `ACTIVE` before registering the pipeline.
