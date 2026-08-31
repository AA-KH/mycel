# TOS 2: Team Common Skills System

## What is a Skill?
A **Skill** in Mycel is a first-class, globally reusable definition of a capability. It answers the question: *"What capability does this entity possess or require?"*

A Skill is independent of who owns it or how it is used. For example, `software_development` is a Skill, whereas an individual agent is the *owner* of that skill, and a tool like `git` is an action the agent might perform to execute that skill.

## What is a Team Skill?
A **Team Skill** represents a baseline expectation for an entire operational domain (Team). When a Team is assigned a Skill (via a `TeamSkillAssignment`), it defines the capabilities the organization expects that team to provide.

## Team Baseline Capability
Teams do not possess literal human skills, they define a *baseline expectation*. If the Engineering Team defines `software_development` with a `proficiency_baseline` of 80, it means the team, on average, expects its members to operate at that level of proficiency. 

## Why Team Skills are Separate from Employee Skills
A Team's baseline defines **intent and expectations** (e.g. "We need people who can code at an 80/100 level"). 
An Employee's skills define **actual, verified capabilities** (e.g. "Kabir can code at a 95/100 level").
By separating the two, Mycel can eventually identify skill gaps, determine when to hire, and orchestrate learning/upskilling workflows for agents.

## Why Skills are Reusable
Skills are defined globally in the `Skill` model so that multiple teams can require the same capability without duplicating the definition. This standardization ensures that when the Engineering Team requires `communication`, it is semantically identical to the `communication` skill required by the Sales Team.

## Shared Skills
Shared skills exist in the `shared` domain (e.g., `communication`, `analysis`, `documentation`). These are common capabilities that span multiple organizational boundaries. A single `Skill` record for `communication` will have many `TeamSkillAssignment` records attaching it to various teams.

## Proficiency Baseline
The `proficiency_baseline` is a strictly bound integer between 0 and 100. It is a metric used for setting capability expectations, ranking requirements, and eventually matching employee performance to team needs.
