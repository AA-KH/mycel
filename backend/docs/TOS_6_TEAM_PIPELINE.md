# TOS 6: Team Pipeline System

## Overview
The Team Pipeline defines **"WHAT sequence of stages does this Team generally follow to transform an input into a validated output?"**

It strictly separates the *Operating Workflow* from the underlying capabilities, tools, knowledge, and reasoning philosophy that power it. The pipeline serves as the structural skeleton that orchestration runtimes will execute.

## Structure
A `TeamPipeline` aggregates ordered, dependency-driven `PipelineStage` nodes. It defines a `PipelineInputContract` and a `PipelineOutputContract` to guarantee that the system will predictably receive standard inputs and deliver reliable artifacts.
